import os
from typing import List, Optional

import bokeh
import numpy as np
import pandas as pd
from navani import echem as ec
from pydatalab import bokeh_plots
from pydatalab.blocks.blocks import DataBlock
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.simple_bokeh_plot import mytheme
from pydatalab.utils import reduce_df_size


def reduce_echem_cycle_sampling(df: pd.DataFrame, num_samples: int = 1000) -> pd.DataFrame:
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
    cycle_list: Optional[List[int]] = None,
    mode: str = "dQ/dV",
    smoothing: bool = True,
    polynomial_spline: int = 3,
    s_spline: float = 1e-5,
    window_size_1: int = 101,
    window_size_2: int = 1001,
    polyorder_1: int = 5,
    polyorder_2: int = 5,
) -> pd.DataFrame:
    """
    Compute differential dQ/dV and dV/dQ based on the input dataframe.

    Args:
        df: The input dataframe containing the raw cycling data.
        cycle_list: List of cycle indices to process, with `None` indicating all cycles.
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

    if mode.lower() == "dv/dq":
        independent_label = "Voltage"
        dependent_label = "Capacity"
    else:
        independent_label = "Capacity"
        dependent_label = "Voltage"

    full_voltage_list = []
    full_dqdv_list = []
    full_cap_list = []
    full_cyc_list = []
    full_hf_cycle_list = []
    half_cycles = []
    voltage_space = []

    if cycle_list is None:
        cycle_list = range(len(df["half cycle"]))

    for item in cycle_list:
        half_cycles.extend([(2 * item) - 1, 2 * item])

    for count, cycle in enumerate(cycle_list):
        idx = df[df["full cycle"] == cycle].index
        df.loc[idx, "colour"] = count

    df = df[df["half cycle"].isin(half_cycles)]

    for cycle in half_cycles:
        try:
            df_cycle = df[df["half cycle"] == cycle]

            voltage_space, dqdv, cap = ec.dqdv_single_cycle(
                df_cycle[independent_label],
                df_cycle[dependent_label],
                polynomial_spline=polynomial_spline,
                window_size_1=window_size_1 if window_size_1 % 2 else window_size_1 + 1,
                polyorder_1=polyorder_1,
                s_spline=s_spline,
                window_size_2=window_size_2 if window_size_2 % 2 else window_size_2 + 1,
                polyorder_2=polyorder_2,
                final_smooth=smoothing,
            )

            mycyc = df_cycle["full cycle"].max()
            cyc = np.full(len(voltage_space), mycyc)

            try:
                mycyc = cycle.max()
            except AttributeError:
                mycyc = cycle

            hf_cyc = np.full(len(voltage_space), mycyc)

            full_voltage_list.extend(voltage_space)
            full_dqdv_list.extend(dqdv)
            full_cap_list.extend(cap)
            full_cyc_list.extend(cyc)
            full_hf_cycle_list.extend(hf_cyc)

            print(f"Printed cycle number {cycle}")

        except ValueError:
            print(f"Tried to print unknown cycle {cycle}")

    differential_key = "dqdv" if independent_label == "Capacity" else "dvdq"

    return pd.DataFrame(
        data={
            "Voltage": full_voltage_list,
            differential_key: full_dqdv_list,
            "Capacity": full_cap_list,
            "full cycle": full_cyc_list,
            "half cycle": full_hf_cycle_list,
        }
    )


# Function to plot normal cycles
def process_norm_df(df, cycle_list):
    """
    Processes user-input df/file for normal printing. Takes in list of full cycles to print, creates a list of half cycles

    Args:
        df: Input df from the user-input file
        cycle_list: User-input field value of the list of cycles they want to print

    Returns:
        A dataframe with all the data for the selected cycles/half-cycles
    """
    half_cycles = (
        []
    )  # Given input is a list of full cycles, we need to prepare list of half-cycles for detailed plotting

    if isinstance(
        cycle_list, list
    ):  # If the input contains a list, implies not all cycles are printed so, print each half-cycle
        for item in cycle_list:
            print(item)
            half_cycles.extend([(2 * item) - 1, 2 * item])
        for count, cycle in enumerate(cycle_list):
            idx = df[df["full cycle"] == cycle].index
            df.loc[idx, "colour"] = count

        df = df[df["half cycle"].isin(half_cycles)]
    return df


class CycleBlock(DataBlock):
    """ "
    Class that contains functions for processing dfs, creating new dfs with different columns (computing dqdv)
    , functions that call bokeh functions with relevant dfs
    """

    blocktype = "cycle"
    description = "Echem cycle"

    accepted_file_extensions = [".mpr", ".txt", ".xls", ".xlsx", ".txt", ".res"]

    defaults = {
        "p_spline": 5,
        "s_spline": 5,
        "win_size_2": 101,
        "win_size_1": 1001,
        "plotmode-dqdv": False,
        "plotmode-dvdq": False,
    }  # values that are set by default if they are not supplied by the dictionary in init()

    def plot_cycle(
        self, voltage_label="Voltage", capacity_label="Capacity", capacity_units="mAh"
    ):

        if "file_id" not in self.data:
            print("No file_id given")
            return None

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        filename = file_info["name"]
        ext = os.path.splitext(filename)[-1].lower()

        if ext not in self.accepted_file_extensions:
            print("Unrecognized filetype")
            return None

        if "cyclenumber" not in self.data:
            self.data["cyclenumber"] = ""  # plot all

        # User list input
        cycle_list = self.data["cyclenumber"]

        df = ec.echem_file_loader(file_info["location"])
        if "time/s" in df:
            df["Time"] = df[
                "time/s"
            ]  # temporary. Navani should give "Time" as a standard field in the future.

        # Reduce df size
        df = reduce_echem_cycle_sampling(df)

        # Take variables from vue, assign them to these variable names 'a, b, c, d' - some of them have to be odd numbers, so that is processed

        b = float(self.data["s_spline"])
        a = int(self.data["p_spline"])
        c = int(self.data["win_size_1"])
        d = int(self.data["win_size_2"])

        # c and b has to be odd
        if (c % 2) == 0:
            c = c + 1
        if (b % 2) == 0:
            b = b + 1

        # Empty input/Print all cycles
        if not isinstance(cycle_list, list) is False:
            cycle_list = list(df["full cycle"].unique())

        df = process_norm_df(df, cycle_list)

        if self.data["plotmode-dqdv"] or self.data["plotmode-dvdq"]:
            differential_df = compute_gpcl_differential(
                df,
                cycle_list,
                polynomial_spline=a,
                s_spline=10 ** (-b),
                window_size_1=c,
                window_size_2=d,
                mode="dQ/dV" if self.data["plotmode-dqdv"] else "dV/dQ",
            )

        if self.data["plotmode-dqdv"]:
            layout = bokeh_plots.double_axes_plot_dvdq(
                df,
                differential_df,
                x_default="Capacity",
            )
        elif self.data["plotmode-dvdq"]:
            layout = bokeh_plots.double_axes_plot(
                df, df2=differential_df, x_options=["Capacity", "Time"], x_default="Capacity"
            )
        # Normal plotting mode
        else:
            layout = bokeh_plots.selectable_axes_plot_colours(
                df,
                x_options=[
                    "Capacity",
                    "Voltage",
                    "Time",
                ],
                y_options=[
                    "Capacity",
                    "Voltage",
                    "Time",
                ],
            )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)

    def to_web(self):
        self.plot_cycle()
        return self.data

    def to_db(self):
        return {
            key: value for (key, value) in self.data.items() if key != "bokeh_plot_data"
        }  # don't save the bokeh plot in the database
