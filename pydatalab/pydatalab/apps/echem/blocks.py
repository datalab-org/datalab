import os
import time
from pathlib import Path
from typing import Any, Dict

import bokeh
import pandas as pd
from navani import echem as ec

from pydatalab import bokeh_plots
from pydatalab.blocks.base import DataBlock
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo
from pydatalab.simple_bokeh_plot import mytheme

from .utils import (
    compute_gpcl_differential,
    filter_df_by_cycle_index,
    reduce_echem_cycle_sampling,
)


class CycleBlock(DataBlock):
    """A data block for processing electrochemical cycling data.

    This class that contains functions for processing dataframes created by navani
    from raw cycler files and plotting them with Bokeh.

    """

    blocktype = "cycle"
    description = "Electrochemical cycling"

    accepted_file_extensions = (
        ".mpr",
        ".txt",
        ".xls",
        ".xlsx",
        ".txt",
        ".res",
        ".csv",
        ".mps",
    )

    cache: Dict[str, Any]

    defaults = {
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

    @classmethod
    def load(cls, filename: str | Path, reload: bool = False):
        """Loads the echem data using navani (or otherwise), summarises it, then caches the results
        to disk with suffixed names.

        Parameters:
            filename: The name of the file to load.
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

        ext = os.path.splitext(filename)[-1].lower()

        if ext not in cls.accepted_file_extensions:
            raise RuntimeError(
                f"Unrecognized filetype {ext}, must be one of {cls.accepted_file_extensions}"
            )

        parsed_file_loc = Path(filename).with_suffix(".RAW_PARSED.pkl")
        cycle_summary_file_loc = Path(filename).with_suffix(".SUMMARY.pkl")

        raw_df = None
        cycle_summary_df = None
        if not reload:
            if parsed_file_loc.exists():
                raw_df = pd.read_pickle(parsed_file_loc)

            if cycle_summary_file_loc.exists():
                cycle_summary_df = pd.read_pickle(cycle_summary_file_loc)

        if raw_df is None:
            if ext == ".csv":
                from pydatalab.apps.echem.palmsens import read_palmsens_csv

                raw_eis_df, raw_df = read_palmsens_csv(filename)
                return raw_df, raw_eis_df
            try:
                LOGGER.debug("Loading file %s", filename)
                start_time = time.time()
                raw_df = ec.echem_file_loader(filename)
                LOGGER.debug(
                    "Loaded file %s in %s seconds",
                    filename,
                    time.time() - start_time,
                )
            except Exception as exc:
                raise RuntimeError(f"Navani raised an error when parsing: {exc}") from exc
            raw_df.to_pickle(parsed_file_loc)

        if cycle_summary_df is None:
            cycle_summary_df = ec.cycle_summary(raw_df)
            cycle_summary_df.to_pickle(cycle_summary_file_loc)

        raw_df = raw_df.filter(required_keys)
        raw_df.rename(columns=keys_with_units, inplace=True)

        cycle_summary_df.rename(columns=keys_with_units, inplace=True)
        cycle_summary_df["cycle index"] = pd.to_numeric(cycle_summary_df.index, downcast="integer")

        return raw_df, cycle_summary_df

    def plot_cycle(self):
        """Plots the electrochemical cycling data from the file ID provided in the request."""
        if "file_id" not in self.data:
            LOGGER.warning("No file_id given")
            return
        file_id = self.data["file_id"]

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

        file_info = get_file_info_by_id(file_id, update_if_live=True)
        filename = file_info["name"]

        reload = False
        if file_info.get("is_live"):
            reload = True

        raw_df, cycle_summary_df = self.load(filename, reload=reload)

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

        layout = bokeh_plots.double_axes_echem_plot(
            df, cycle_summary=cycle_summary_df, mode=mode, normalized=bool(characteristic_mass_g)
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
        return

    @property
    def plot_functions(self):
        return (self.plot_cycle,)
