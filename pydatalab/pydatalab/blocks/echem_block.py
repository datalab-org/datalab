import os
from typing import Any, Dict, List, Optional

import bokeh
import numpy as np
import pandas as pd
from navani import echem as ec

from pydatalab import bokeh_plots
from pydatalab.blocks.blocks import DataBlock
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.simple_bokeh_plot import mytheme
from pydatalab.utils import reduce_df_size


def reduce_echem_cycle_sampling(df: pd.DataFrame, num_samples: int = 5000) -> pd.DataFrame:
    """Reduce number of data points per cycle.

    Parameters:
        df: The echem dataframe to reduce, which must have cycling data stored
            under a `"full cycle"` column.
        num_displayed: The maximum number of sample points to include per cycle.

    Returns:
        The output dataframe.

    """

    number_of_cycles = df["full cycle"].nunique()

    if number_of_cycles >= 1:
        df = reduce_df_size(df, num_samples)
    return df


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
        y_label = "Voltage"
        x_label = "Capacity"
        yp_label = "dvdq"
    else:
        y_label = "Capacity"
        x_label = "Voltage"
        yp_label = "dqdv"

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

        differential_df = differential_df.append(
            pd.DataFrame(
                {
                    x_label: x,
                    y_label: y,
                    yp_label: yp,
                    "full cycle": cycle_index_array,
                    "half cycle": half_cycle_index_array,
                }
            )
        )

    return differential_df


def filter_df_by_cycle_index(
    df: pd.DataFrame, cycle_list: Optional[List[int]] = None
) -> pd.DataFrame:
    """Filters the input dataframe by the chosen rows in the `cycle_list`.

    Args:
        df: The input dataframe to filter. Must have the column "half cycle".
        cycle_list: The provided list of cycle indices to keep.

    Returns:
        A dataframe with all the data for the selected cycles.

    """
    if cycle_list is None:
        return df

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

    def plot_cycle(self):
        """Plots the electrochemical cycling data from the file ID provided in the request."""

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

        if "file_id" not in self.data:
            LOGGER.warning("No file_id given")
            return

        derivative_modes = (None, "dQ/dV", "dV/dQ")

        if self.data["derivative_mode"] not in derivative_modes:
            LOGGER.warning(
                "Invalid derivative_mode provided: %s. Expected one of %s. Falling back to `None`.",
                self.data["derivative_mode"],
                derivative_modes,
            )
            self.data["derivative_mode"] = None

        file_id = self.data["file_id"]

        if self.data["derivative_mode"] is None:
            mode = "normal"
        else:
            mode = self.data["derivative_mode"]

        # User list input
        cycle_list = self.data.get("cyclenumber", None)
        if not isinstance(cycle_list, list):
            cycle_list = None

        # retrieve bokeh_plot_data from the cache if it has already been generated for a given file, mode, and settings:
        if (
            self.cache.get("bokeh_plot_data", {}).get(file_id, {}).get(mode, None)
            and cycle_list == self.cache.get("cycle_list", [])
            and self.cache.get("win_size_1") == self.data["win_size_1"]
            and self.cache.get("s_spline") == self.data["s_spline"]
        ):
            self.data["bokeh_plot_data"] = self.cache["bokeh_plot_data"][file_id][mode]
            return

        self.cache["cycle_list"] = cycle_list
        self.cache["win_size_1"] = self.data["win_size_1"]
        self.cache["s_spline"] = self.data["s_spline"]

        file_info = get_file_info_by_id(file_id, update_if_live=True)
        filename = file_info["name"]
        ext = os.path.splitext(filename)[-1].lower()

        if ext not in self.accepted_file_extensions:
            LOGGER.warning(
                f"Unrecognized filetype {ext}, must be one of {self.accepted_file_extensions}"
            )
            return

        if file_id in self.cache.get("parsed_file", {}):
            raw_df = self.cache["parsed_file"][file_id]
        else:
            raw_df = ec.echem_file_loader(file_info["location"])
            if "time/s" in raw_df:
                # temporary. Navani should give "Time" as a standard field in the future.
                raw_df["Time"] = raw_df["time/s"]
            raw_df = raw_df.filter(required_keys)
            self.cache["parsed_file"] = raw_df

        df = filter_df_by_cycle_index(raw_df, cycle_list)

        if mode in ("dQ/dV", "dV/dQ"):

            df = compute_gpcl_differential(
                df,
                mode=mode,
                polynomial_spline=int(self.data["p_spline"]),
                s_spline=10 ** (-float(self.data["s_spline"])),
                window_size_1=int(self.data["win_size_1"]),
                window_size_2=int(self.data["win_size_2"]),
            )

        # Reduce df size to ~1000 rows by default
        df = reduce_echem_cycle_sampling(df)

        layout = bokeh_plots.double_axes_echem_plot(df, mode=mode)

        if "bokeh_plot_data" not in self.cache:
            self.cache["bokeh_plot_data"] = {}

        if file_id not in self.cache["bokeh_plot_data"]:
            self.cache["bokeh_plot_data"][file_id] = {}

        self.cache["bokeh_plot_data"][file_id][mode] = bokeh.embed.json_item(layout, theme=mytheme)
        self.data["bokeh_plot_data"] = self.cache["bokeh_plot_data"][file_id][mode]
        return

    @property
    def plot_functions(self):
        return (self.plot_cycle,)
