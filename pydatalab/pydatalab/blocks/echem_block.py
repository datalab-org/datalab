import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import bokeh
import numpy as np
import pandas as pd
from bson import ObjectId
from navani import echem as ec

from pydatalab import bokeh_plots
from pydatalab.blocks.blocks import DataBlock
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo
from pydatalab.simple_bokeh_plot import mytheme
from pydatalab.utils import reduce_df_size


def reduce_echem_cycle_sampling(df: pd.DataFrame, num_samples: int = 100) -> pd.DataFrame:
    """Reduce number of cycles to at most `num_samples` points per half cycle. Will 
    keep the endpoint values of each half cycle.

    Parameters:
        df: The echem dataframe to reduce, which must have cycling data stored
            under a `"half cycle"` column.
        num_samples: The maximum number of sample points to include per cycle.

    Returns:
        The output dataframe.

    """

    return_df = pd.DataFrame([])

    for _, half_cycle in df.groupby("half cycle"):
        return_df = pd.concat([return_df, reduce_df_size(half_cycle, num_samples, endpoint=True)])

    return return_df


def compute_gpcl_differential(
    df: pd.DataFrame,
    mode: str = "dQ/dV",
    smoothing: bool = True,
    polynomial_spline: int = 3,
    s_spline: float = 1e-5,
    window_size_1: int = 101,
    window_size_2: int = 1001,
    polyorder_1: int = 5,
    polyorder_2: int = 5,
    use_normalized_capacity: bool = False,
) -> pd.DataFrame:
    """Compute differential dQ/dV or dV/dQ for the input dataframe.

    Args:
        df: The input dataframe containing the raw cycling data.
        mode: Either 'dQ/dV' or 'dV/dQ'. Invalid inputs will default to 'dQ/dV'.
        smoothing: Whether or not to apply additional smoothing to the output differential curve.
        polynomial_spline: The degree of the B-spline fit used by navani.
        s_spline: The smoothing parameter used by navani.
        window_size_1: The window size for the `savgol` filter when smoothing the capacity.
        window_size_2: The window size for the `savgol` filter when smoothing the final differential.
        polyorder_1: The polynomial order for the `savgol` filter when smoothing the capacity.
        polyorder_2: The polynomial order for the `savgol` filter when smoothing the final differential.

    Returns:
        A data frame containing the voltages, capacities and requested differential
        on the reduced cycle list.

    """
    if len(df) < 2:
        LOGGER.debug(
            f"compute_gpcl_differential called on dataframe with length {len(df)}, too small to calculate derivatives"
        )
        return df

    if mode.lower().replace("/", "") == "dvdq":
        y_label = "voltage (V)"
        x_label = "capacity (mAh/g)" if use_normalized_capacity else "capacity (mAh)"
        yp_label = "dV/dQ (V/mA)"
    else:
        y_label = "capacity (mAh/g)" if use_normalized_capacity else "capacity (mAh)"
        x_label = "voltage (V)"
        yp_label = "dQ/dV (mA/V)"

    smoothing_parameters = {
        "polynomial_spline": polynomial_spline,
        "s_spline": s_spline,
        "window_size_1": window_size_1 if window_size_1 % 2 else window_size_1 + 1,
        "window_size_2": window_size_2 if window_size_2 % 2 else window_size_2 + 1,
        "polyorder_1": polyorder_1,
        "polyorder_2": polyorder_2,
        "final_smooth": smoothing,
    }

    differential_df = pd.DataFrame()

    # Loop over distinct half cycles
    for cycle in df["half cycle"].unique():
        # Extract all segments corresponding to this half cycle index
        df_cycle = df[df["half cycle"] == cycle]

        # Compute the desired derivative
        try:
            x, yp, y = ec.dqdv_single_cycle(
                df_cycle[y_label], df_cycle[x_label], **smoothing_parameters
            )
        except TypeError as e:
            LOGGER.debug(
                f"""Calculating derivative {mode} of half_cycle {cycle} failed with the following error (likely it is a rest or voltage hold):
                 {e}
                Skipping derivative calculation for this half cycle."""
            )
            continue

        # Set up an array per cycle segment that stores the cycle and half-cycle index
        cycle_index = df_cycle["full cycle"].max()
        cycle_index_array = np.full(len(x), int(cycle_index), dtype=int)
        half_cycle_index_array = np.full(len(x), int(cycle), dtype=int)

        differential_df = pd.concat(
            [
                differential_df,
                pd.DataFrame(
                    {
                        x_label: x,
                        y_label: y,
                        yp_label: yp,
                        "full cycle": cycle_index_array,
                        "half cycle": half_cycle_index_array,
                    }
                ),
            ]
        )

    return differential_df


def filter_df_by_cycle_index(
    df: pd.DataFrame, cycle_list: Optional[List[int]] = None
) -> pd.DataFrame:
    """Filters the input dataframe by the chosen rows in the `cycle_list`.
    If `half_cycle` is a column in the df, it will be used for filtering,
    otherwise `cycle index` will be used.

    Args:
        df: The input dataframe to filter. Must have the column "half cycle".
        cycle_list: The provided list of cycle indices to keep.

    Returns:
        A dataframe with all the data for the selected cycles.

    """
    if cycle_list is None:
        return df

    if "half cycle" not in df.columns:
        if "cycle index" not in df.columns:
            raise ValueError(
                "Input dataframe must have either 'half cycle' or 'cycle index' column"
            )
        return df[df["cycle index"].isin(i for i in cycle_list)]

    try:
        half_cycles = [i for item in cycle_list for i in [(2 * int(item)) - 1, 2 * int(item)]]
    except ValueError as exc:
        raise ValueError(
            f"Unable to parse `cycle_list` as integers: {cycle_list}. Error: {exc}"
        ) from exc
    return df[df["half cycle"].isin(half_cycles)]


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

    def _load(self, file_id: Union[str, ObjectId], reload: bool = False):
        """Loads the echem data using navani, summarises it, then caches the results
        to disk with suffixed names.

        Parameters:
            file_id: The ID of the file to load.
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

        file_info = get_file_info_by_id(file_id, update_if_live=True)
        filename = file_info["name"]

        if file_info.get("is_live"):
            reload = True

        ext = os.path.splitext(filename)[-1].lower()

        if ext not in self.accepted_file_extensions:
            raise RuntimeError(
                f"Unrecognized filetype {ext}, must be one of {self.accepted_file_extensions}"
            )

        parsed_file_loc = Path(file_info["location"]).with_suffix(".RAW_PARSED.pkl")
        cycle_summary_file_loc = Path(file_info["location"]).with_suffix(".SUMMARY.pkl")

        raw_df = None
        cycle_summary_df = None
        if not reload:
            if parsed_file_loc.exists():
                raw_df = pd.read_pickle(parsed_file_loc)

            if cycle_summary_file_loc.exists():
                cycle_summary_df = pd.read_pickle(cycle_summary_file_loc)

        if raw_df is None:
            try:
                LOGGER.debug("Loading file %s", file_info["location"])
                start_time = time.time()
                raw_df = ec.echem_file_loader(file_info["location"])
                LOGGER.debug(
                    "Loaded file %s in %s seconds",
                    file_info["location"],
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

        raw_df, cycle_summary_df = self._load(file_id)

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

        # Reduce df size to 100 points per cycle by default
        df = reduce_echem_cycle_sampling(df, num_samples=100)

        layout = bokeh_plots.double_axes_echem_plot(
            df, cycle_summary=cycle_summary_df, mode=mode, normalized=bool(characteristic_mass_g)
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
        return

    @property
    def plot_functions(self):
        return (self.plot_cycle,)
