import os
import warnings
from pathlib import Path
from typing import Any

import bokeh
import pandas as pd
from bson import ObjectId
from navani import echem as ec

from pydatalab import bokeh_plots
from pydatalab.blocks.base import DataBlock
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo

from .utils import (
    compute_gpcl_differential,
    filter_df_by_cycle_index,
    reduce_echem_cycle_sampling,
)


class CycleBlock(DataBlock):
    """A data block for processing electrochemical cycling data.

    This class that contains functions for processing dataframes created by navani
    from raw cycler files and plotting them with Bokeh.

    Navani documentation: https://be-smith.github.io/navani/

    The file formats currently supported are:

    - Biologic (.mpr) - requires galvani https://github.com/echemdata/galvani
    - Arbin (.res, .xls and .xlsx) - the .res format requires galvani https://github.com/echemdata/galvani
    - Neware (.nda, .ndax)
    - Ivium (.txt)
    - Lanhe/Lande (.xls, .xlsx) - most formats, certain exports may not work depending on the software version or settings
    - Preprocessed (.csv) - CSV files with appropriate columns ['Capacity', 'Voltage', 'half cycle', 'full cycle', 'Current', 'state']

    """

    blocktype = "cycle"
    name = "Electrochemical cycling"
    description = """This block can plot data from electrochemical cycling experiments from many different cycler's file formats.
    The file formats currently supported are:

    - Biologic (.mpr)
    - Arbin (.res, .xls and .xlsx)
    - Neware (.nda, .ndax)
    - Ivium (.txt)
    - Lanhe/Lande (.xls, .xlsx)
    - Preprocessed (.csv) (previously extracted by navani or other tools)

    """

    accepted_file_extensions = (
        ".mpr",
        ".txt",
        ".xls",
        ".xlsx",
        ".res",
        ".nda",
        ".ndax",
        ".csv",
    )

    defaults: dict[str, Any] = {
        "p_spline": 5,
        "s_spline": 5,
        "win_size_2": 101,
        "win_size_1": 1001,
        "derivative_mode": None,
    }

    def _get_characteristic_mass_g(self):
        # return {"characteristic_mass": 1000}
        doc = flask_mongo.db.items.find_one(
            {"item_id": self.data["item_id"]}, {"characteristic_mass": 1}
        )
        characteristic_mass_mg = doc.get("characteristic_mass", None)
        if characteristic_mass_mg:
            return characteristic_mass_mg / 1000.0
        return None

    def _load(self, file_ids: list[ObjectId] | ObjectId, reload: bool = True):
        """Loads the echem data using navani, summarises it, then caches the results
        to disk with suffixed names.

        Parameters:
            file_ids: The IDs of the files to load.
            reload: Whether to reload the data from the file, or use the cached version, if available.

        """

        required_keys = (
            "Time",
            "Voltage",
            "Capacity",
            "Current",
            "dqdv",
            "dvdq",
            "half cycle",
            "full cycle",
        )

        keys_with_units = {
            "Time": "time (s)",
            "Voltage": "voltage (V)",
            "Capacity": "capacity (mAh)",
            "Current": "current (mA)",
            "Charge Capacity": "charge capacity (mAh)",
            "Discharge Capacity": "discharge capacity (mAh)",
            "dqdv": "dQ/dV (mA/V)",
            "dvdq": "dV/dQ (V/mA)",
        }
        if isinstance(file_ids, ObjectId):
            file_ids = [file_ids]

        raw_df = None
        cycle_summary_df = None

        if len(file_ids) == 1:
            file_info = get_file_info_by_id(file_ids[0], update_if_live=True)
            filename = file_info["name"]

            if file_info.get("is_live"):
                reload = True

            ext = os.path.splitext(filename)[-1].lower()

            if ext not in self.accepted_file_extensions:
                raise RuntimeError(
                    f"Unrecognized filetype {ext}, must be one of {self.accepted_file_extensions}"
                )

            parsed_file_loc = Path(file_info["location"]).with_suffix(".RAW_PARSED.pkl")

            if not reload:
                if parsed_file_loc.exists():
                    raw_df = pd.read_pickle(parsed_file_loc)  # noqa: S301

            if raw_df is None:
                try:
                    raw_df = ec.echem_file_loader(file_info["location"])
                except Exception as exc:
                    raise RuntimeError(f"Navani raised an error when parsing: {exc}") from exc
                raw_df.to_pickle(parsed_file_loc)

        elif isinstance(file_ids, list) and len(file_ids) > 1:
            # Multi-file logic
            file_infos = [get_file_info_by_id(fid, update_if_live=True) for fid in file_ids]
            locations = [info["location"] for info in file_infos]

            if raw_df is None:
                try:
                    LOGGER.debug("Loading multiple echem files with navani: %s", locations)
                    # Catch the navani warning when stitching multiple files together and calculating new capacity
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message=(
                                "Capacity columns are not equal, replacing with new capacity column calculated from current and time columns and renaming the old capacity column to Old Capacity"
                            ),
                            category=UserWarning,
                        )
                        raw_df = ec.multi_echem_file_loader(locations)
                except Exception as exc:
                    raise RuntimeError(
                        f"Navani raised an error when parsing multiple files: {exc}"
                    ) from exc

        elif not isinstance(file_ids, list):
            raise ValueError("Invalid file_ids type. Expected list of strings.")
        elif len(file_ids) == 0:
            raise ValueError("Invalid file_ids value. Expected non-empty list of strings.")

        if cycle_summary_df is None and raw_df is not None:
            try:
                cycle_summary_df = ec.cycle_summary(raw_df)
            except Exception as exc:
                warnings.warn(f"Cycle summary generation failed with error: {exc}")

        if raw_df is not None:
            raw_df = raw_df.filter(required_keys)
            raw_df.rename(columns=keys_with_units, inplace=True)
        else:
            raise ValueError("Invalid raw_df value. Expected non-empty DataFrame.")

        if cycle_summary_df is not None:
            cycle_summary_df.rename(columns=keys_with_units, inplace=True)
            cycle_summary_df["cycle index"] = pd.to_numeric(
                cycle_summary_df.index, downcast="integer"
            )

        return raw_df, cycle_summary_df

    def plot_cycle(self):
        """Plots the electrochemical cycling data from the file ID provided in the request."""
        # Legacy support for when file_id was used
        if self.data.get("file_id") is not None and not self.data.get("file_ids"):
            LOGGER.info("Legacy file upload detected, using file_id")
            file_ids = [self.data["file_id"]]

        else:
            if "file_ids" not in self.data:
                LOGGER.warning("No file_ids given, skipping plot.")
                return
            if self.data["file_ids"] is None or len(self.data["file_ids"]) == 0:
                LOGGER.warning("Empty file_ids list given, skipping plot.")
                return

            file_ids = self.data["file_ids"]

        derivative_modes = (None, "dQ/dV", "dV/dQ", "final capacity")

        if self.data["derivative_mode"] not in derivative_modes:
            LOGGER.warning(
                "Invalid derivative_mode provided: %s. Expected one of %s. Falling back to `None`.",
                self.data["derivative_mode"],
                derivative_modes,
            )
            self.data["derivative_mode"] = None

        if self.data["derivative_mode"] is None:
            mode = "normal"
        else:
            mode = self.data["derivative_mode"]

        # User list input
        cycle_list = self.data.get("cyclenumber", None)
        if not isinstance(cycle_list, list):
            cycle_list = None

        raw_dfs = {}
        cycle_summary_dfs = {}

        # Single/multi mode gets a single dataframe - returned as a dict for consistency
        if self.data.get("mode") == "multi" or self.data.get("mode") == "single":
            file_info = get_file_info_by_id(file_ids[0], update_if_live=True)
            filename = file_info["name"]
            raw_df, cycle_summary_df = self._load(file_ids=file_ids)

            characteristic_mass_g = self._get_characteristic_mass_g()

            if characteristic_mass_g:
                raw_df["capacity (mAh/g)"] = raw_df["capacity (mAh)"] / characteristic_mass_g
                raw_df["current (mA/g)"] = raw_df["current (mA)"] / characteristic_mass_g
                if cycle_summary_df is not None:
                    cycle_summary_df["charge capacity (mAh/g)"] = (
                        cycle_summary_df["charge capacity (mAh)"] / characteristic_mass_g
                    )
                    cycle_summary_df["discharge capacity (mAh/g)"] = (
                        cycle_summary_df["discharge capacity (mAh)"] / characteristic_mass_g
                    )

            if self.data.get("mode") == "multi":
                p = Path(filename)
                filename = f"{p.stem}_merged{p.suffix}"
                raw_dfs[filename] = raw_df
                cycle_summary_dfs[filename] = cycle_summary_df
            elif self.data.get("mode") == "single":
                raw_dfs[filename] = raw_df
                cycle_summary_dfs[filename] = cycle_summary_df

        else:
            raise ValueError(f"Invalid mode {self.data.get('mode')}")

        # Load comparison files if provided
        comparison_file_ids = self.data.get("comparison_file_ids", [])
        if comparison_file_ids and len(comparison_file_ids) > 0:
            # TODO (ben smith) Currently can't load in different masses for different files in comparison mode
            for file in comparison_file_ids:
                try:
                    file_info = get_file_info_by_id(file, update_if_live=True)
                    filename = file_info["name"]
                    comparison_raw_df, comparison_cycle_summary_df = self._load(
                        file_ids=[file], reload=False
                    )
                    # Mark comparison files with a prefix to distinguish them
                    raw_dfs[f"[Comparison] {filename}"] = comparison_raw_df
                    cycle_summary_dfs[f"[Comparison] {filename}"] = comparison_cycle_summary_df
                except Exception as exc:
                    LOGGER.error("Failed to load comparison file %s: %s", file, exc)

        dfs = {}
        for filename, raw_df in raw_dfs.items():
            cycle_summary_df = cycle_summary_dfs.get(filename)
            df = filter_df_by_cycle_index(raw_df, cycle_list)
            if cycle_summary_df is not None:
                cycle_summary_df = filter_df_by_cycle_index(cycle_summary_df, cycle_list)

            if mode in ("dQ/dV", "dV/dQ"):
                df = compute_gpcl_differential(
                    df,
                    mode=mode,
                    polynomial_spline=int(self.data["p_spline"]),
                    s_spline=10 ** (-float(self.data["s_spline"])),
                    window_size_1=int(self.data["win_size_1"]),
                    window_size_2=int(self.data["win_size_2"]),
                    use_normalized_capacity=bool(characteristic_mass_g),
                )
            # Reduce df size to 100 points per cycle by default if there are more than a 100k points
            if len(df) > 1e5:
                df = reduce_echem_cycle_sampling(df, num_samples=100)
                LOGGER.debug("Reduced df size, df length: %d", len(df))
            df["filename"] = filename
            cycle_summary_df["filename"] = filename
            dfs[filename] = df
            cycle_summary_dfs[filename] = cycle_summary_df

        # Determine plotting mode - if comparison files exist, use comparison mode
        plotting_mode = (
            "comparison"
            if comparison_file_ids and len(comparison_file_ids) > 0
            else self.data.get("mode")
        )

        layout = bokeh_plots.double_axes_echem_plot(
            dfs=list(dfs.values()),
            cycle_summary_dfs=list(cycle_summary_dfs.values()),
            mode=mode,
            normalized=bool(characteristic_mass_g),
            plotting_mode=plotting_mode,
        )

        if layout is not None:
            # Don't overwrite the previous plot data in cases where the plot is not generated
            # for a 'normal' reason
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(
                layout, theme=bokeh_plots.DATALAB_BOKEH_THEME
            )
        return

    @property
    def plot_functions(self):
        return (self.plot_cycle,)
