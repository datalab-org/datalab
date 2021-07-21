import os

import bokeh
import bokeh_plots
import numpy as np
import pandas as pd
from blocks import DataBlock
from file_utils import get_file_info_by_id
from navani import echem as ec
from scipy.interpolate import splev, splrep
from scipy.signal import savgol_filter
from simple_bokeh_plot import mytheme

DISPLAYED_DATA_POINTS = 1000  # The number of data points to display in the frontend


def reduce_size(df):
    # Find the number of cycles, if it's greater than 10, take out every second row

    number_of_cycles = df["full cycle"].nunique()
    rows = len(df)

    if number_of_cycles >= 1:
        df = bokeh_plots.reduce_df_size(df, DISPLAYED_DATA_POINTS)
    return df


def multi_dqdv_plot(
    df,
    cycle_list,
    polynomial_spline,
    s_spline,
    window_size_1,
    window_size_2,
    polyorder_1=5,
    polyorder_2=5,
    capacity_label="Capacity",
    voltage_label="Voltage",
    final_smooth=True,
):

    full_voltage_list = []
    full_dqdv_list = []
    full_cap_list = []
    full_cyc_list = []
    full_hf_cycle_list = []
    half_cycles = []
    myvoltage = []

    for item in cycle_list:
        half_cycles.extend([(2 * item) - 1, 2 * item])

    for count, cycle in enumerate(cycle_list):
        idx = df[df["full cycle"] == cycle].index
        df.loc[idx, "colour"] = count

    df = df[df["half cycle"].isin(half_cycles)]

    for cycle in half_cycles:
        try:
            df_cycle = df[df["half cycle"] == cycle]

            myvoltage, dqdv, cap = ec.dqdv_single_cycle(
                df_cycle[capacity_label],
                df_cycle[voltage_label],
                polynomial_spline=polynomial_spline,
                window_size_1=window_size_1,
                polyorder_1=polyorder_1,
                s_spline=s_spline,
                window_size_2=window_size_2,
                polyorder_2=polyorder_2,
                final_smooth=final_smooth,
            )

            # print(type(full_voltage_list))
            x_volt = np.linspace(
                min(df_cycle[voltage_label]), max(df_cycle[voltage_label]), num=int(1e4)
            )

            mycyc = df_cycle["full cycle"].max()
            cyc = np.full(len(x_volt), mycyc)

            try:
                mycyc = cycle.max()
            except AttributeError:
                mycyc = cycle

            hf_cyc = np.full(len(x_volt), mycyc)

            full_voltage_list.extend(myvoltage)
            full_dqdv_list.extend(dqdv)
            full_cap_list.extend(cap)
            full_cyc_list.extend(cyc)
            full_hf_cycle_list.extend(hf_cyc)

            print(f"Printed cycle number {cycle}")
        except ValueError:
            print("Tried to print unkown cycle")
    return (
        full_voltage_list,
        full_dqdv_list,
        full_cap_list,
        full_cyc_list,
        full_hf_cycle_list,
    )


# Function to plot normal cycles
def send_bokeh_norm(df, cycle_list):
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


# Function to plot dqdv
def send_bokeh_dqdv(df, cycle_list, polynomial_spline, win_size_1, win_size_2, s_spline):
    # check if there is a list of cycles

    (
        full_voltage_list,
        full_dqdv_list,
        full_cap_list,
        full_cyc_list,
        full_hf_cycle_list,
    ) = multi_dqdv_plot(
        df,
        cycle_list,
        capacity_label="Capacity",
        voltage_label="Voltage",
        polynomial_spline=polynomial_spline,
        s_spline=s_spline,
        window_size_1=win_size_1,
        polyorder_1=5,  # polyorders are normally 5, no difference with other values
        window_size_2=win_size_2,
        polyorder_2=5,
        final_smooth=True,
    )

    dict = {
        "Voltage": full_voltage_list,
        "dqdv": full_dqdv_list,
        "Capacity": full_cap_list,
        "full cycle": full_cyc_list,
        "half cycle": full_hf_cycle_list,
    }
    final_df = pd.DataFrame(dict)
    return final_df


# else print all cycles


# function to plot dvdq - essentially uses multi-dqdv-plot but capacity and voltage is flipped
def send_bokeh_dvdq(df, cycle_list, polynomial_spline, win_size_1, win_size_2, s_spline):

    (
        full_voltage_list,
        full_dqdv_list,
        full_cap_list,
        full_cyc_list,
        full_hf_cycle_list,
    ) = multi_dqdv_plot(
        df,
        cycle_list,
        capacity_label="Voltage",
        voltage_label="Capacity",
        polynomial_spline=polynomial_spline,
        s_spline=s_spline,
        window_size_1=win_size_1,
        polyorder_1=5,
        window_size_2=win_size_2,
        polyorder_2=5,
        final_smooth=True,
    )

    dict = {
        "Voltage": full_voltage_list,
        "dqdv": full_dqdv_list,
        "Capacity": full_cap_list,
        "full cycle": full_cyc_list,
        "half cycle": full_hf_cycle_list,
    }
    final_df = pd.DataFrame(dict)
    return final_df


class CycleBlock(DataBlock):
    blocktype = "cycle"
    description = "Echem cycle"

    accepted_file_extensions = [".mpr", ".txt", ".xls", ".xlsx", ".txt", ".res"]

    def plot_cycle(self, voltage_label="Voltage", capacity_label="Capacity", capacity_units="mAh"):

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

        # Reduce df size
        df = reduce_size(df)

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

        # If user has activated dqdv mode
        if self.data["plotmode-dqdv"]:
            # Empty input/Print all cycles
            if isinstance(cycle_list, list) is False:
                cycle_list = list(df["full cycle"].unique())

            dqdv_df = send_bokeh_dqdv(
                df,
                cycle_list,
                polynomial_spline=a,
                s_spline=10 ** (-b),
                win_size_1=c,
                win_size_2=d,
            )
            df = send_bokeh_norm(df, cycle_list)
            # Send to bokeh for plotting
            layout = bokeh_plots.double_axes_plot(
                df, df2=dqdv_df, y_default="Voltage", x_axis_label="Capacity", x="dqdv"
            )
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
        # If user has activated dvdq mode
        elif self.data["plotmode-dvdq"]:
            if isinstance(cycle_list, list) is False:
                cycle_list = list(df["full cycle"].unique())

            dvdq_df = send_bokeh_dvdq(
                df,
                cycle_list,
                polynomial_spline=a,
                s_spline=10 ** (-b),
                win_size_1=c,
                win_size_2=d,
            )

            df = send_bokeh_norm(df, cycle_list)
            layout = bokeh_plots.double_axes_plot_dvdq(
                df,
                dvdq_df,
                x_default="Capacity",
            )
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=mytheme)
        # Normal plotting mode
        else:
            df = send_bokeh_norm(df, cycle_list)

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
