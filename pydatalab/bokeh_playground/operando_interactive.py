import datetime
import glob
import re
from os.path import join as j

import numpy as np
import pandas as pd
from bokeh.events import DoubleTap
from bokeh.layouts import column, gridplot
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    CrosshairTool,
    HoverTool,
    LinearColorMapper,
)
from bokeh.models.callbacks import CustomJS
from bokeh.palettes import viridis
from bokeh.plotting import figure, show, output_file, save
from neware_reader.neware import nda_to_csv, read_nda


def read_xrd_log(xrd_log_filename):
    # read in log file
    df_log = pd.read_csv(
        xrd_log_filename,
        sep=",",
        skiprows=1,
        names=["scan_number", "cell_name", "start_time", "end_time"],
        parse_dates=["start_time", "end_time"],
        engine="python",
        comment="#",
    )

    # average the start and end time of each scan:
    df_log["xrd_timestamp"] = df_log.start_time + (df_log.end_time - df_log.start_time) / 2

    return df_log


def read_echem(echem_filename, time_offset=datetime.timedelta(0)):
    """time offset is the time on the echem computer minus the time on the xrd computer"""
    # read in echem data
    df_echem = read_nda(echem_filename)
    df_echem["timestamp"] = pd.to_datetime(df_echem["timestamp"]) - time_offset
    df_echem = df_echem.rename(columns={"timestamp": "echem_timestamp"})
    elapsed_timedeltas = df_echem.echem_timestamp - df_echem.echem_timestamp.iloc[0]
    df_echem["elapsed_time_hours"] = [delta.total_seconds() / 3600 for delta in elapsed_timedeltas]

    return df_echem


def merge_xrd_echem_dataframes(df_xrd_log, df_echem, fill_gaps=True):
    """merges two dataframes, the first with xrd log information and the second with echem.
    The new data frame will have one row for each row in df_xrd_log, with the nearest time echem
    being assigned. fill_gaps can be specified to find any gaps that are greater than 2x the normal spacing
    of the patterns and fill in blank rows of xrd spaced in approximately the same manner as the xrd data.
    """
    print("test")
    if fill_gaps:

        pdb.set_trace()
        timesteps = df_xrd_log.xrd_timestamp.diff()
        median_timestep = timesteps.median()

        # a gap is anywhere the time step is more than twice normal
        gap_indices = timesteps[timesteps > 2 * median_timestep].index

        print(f"found {len(gap_indices)} gaps, filling them in!")

        dfs_to_insert = []
        for index in gap_indices:
            new_datetimes = np.arange(
                df_xrd_log.iloc[index - 1].xrd_timestamp,
                df_xrd_log.iloc[index].xrd_timestamp,
                median_timestep,
            )

            df_xrd_log_insert = pd.DataFrame(
                dict(
                    scan_number=None,
                    cell_name=df_xrd_log.cell_name.iloc[0],
                    xrd_timestamp=new_datetimes[1:],
                )
            )
            dfs_to_insert.append(df_xrd_log_insert)

        df_xrd_log = pd.concat([df_xrd_log] + dfs_to_insert).sort_values(
            by="xrd_timestamp", ignore_index=True
        )

    df_merged = pd.merge_asof(
        df_xrd_log,
        df_echem,
        left_on="xrd_timestamp",
        right_on="echem_timestamp",
        direction="nearest",
    )

    return df_merged


def read_xye_files(scan_numbers, file_base="."):
    # can definitely be optimized to improve speed

    # get the files
    dfs = []
    for i, scan_number in enumerate(scan_numbers):

        # set any missing scans to nan
        if scan_number == None:
            # THIS WILL NOT WORK IF THE FIRST SCAN IS NaN
            df = pd.DataFrame(dict(twotheta=dfs[0].twotheta, intensity=0))
            df["pattern_index"] = i

        else:
            fn = j(file_base, f"{scan_number}-mythen_summed.dat")
            df = pd.read_csv(fn, comment="'", sep=r"\s+", names=["twotheta", "intensity", "error"])
            df["pattern_index"] = i
        dfs.append(df)

    all_xrd_data = np.zeros((len(dfs), len(df)))
    for i, df in enumerate(dfs):
        all_xrd_data[i] = df["intensity"]
    return dfs[0].twotheta, all_xrd_data


def create_interactive_plot(
    xrd_log_filename,
    echem_filename,
    file_base=".",
    time_offset=datetime.timedelta(0),
    cutoff_index=5000,
    starting_intensity_max=None,
    html_output_file="operando_diffraction.html",
    show_html=True,
    fill_gaps=True,
):
    output_file(html_output_file)

    df_xrd_log = read_xrd_log(xrd_log_filename)
    df_echem = read_echem(echem_filename, time_offset)

    df_merged = merge_xrd_echem_dataframes(df_xrd_log, df_echem, fill_gaps=fill_gaps)

    twotheta, all_xrd_data = read_xye_files(df_merged.scan_number, file_base)

    if starting_intensity_max == None:
        starting_intensity_max = all_xrd_data.max()

    # cutoff the end of the data for visualization
    twotheta = twotheta[:cutoff_index]
    all_xrd_data = all_xrd_data[:, :cutoff_index]

    # set up the heatmap
    heatmap = figure(
        x_axis_label="2theta",
        tooltips=[("pattern index", "$y{0}")],
        active_drag="box_zoom",
        plot_height=400,
    )
    heatmap.x_range.range_padding = heatmap.y_range.range_padding = 0

    color_mapper = LinearColorMapper(high=starting_intensity_max, low=0, palette="Viridis256")

    heatmap.image(
        image=[all_xrd_data],  # all_xrd_data must be wrapped in a list, for some reason
        x=twotheta.min(),
        y=0,
        dw=twotheta.max() - twotheta.min(),
        dh=len(all_xrd_data),
        color_mapper=color_mapper,
        level="image",
    )

    heatmap.grid.grid_line_width = 0
    color_bar = ColorBar(color_mapper=color_mapper)  # , label_standoff=12)
    heatmap.add_layout(color_bar, "right")

    # set up single diffraction pattern plot on top
    line_source = ColumnDataSource(
        data={"twotheta": twotheta, "intensity": all_xrd_data[0]}
    )  # start with displaying the first pattern
    diffraction_line_plot = figure(
        # x_axis_label="2theta",
        y_axis_label="intensity",
        aspect_ratio=2,
        x_range=heatmap.x_range,  # link x of heatmap and diffraction line plot
        y_range=(0, starting_intensity_max),
    )
    diffraction_line_plot.line(x="twotheta", y="intensity", source=line_source)

    # set up the echem plot on the left
    echemplot = figure(
        x_axis_label="voltage (V)",
        y_axis_label="pattern index",
        y_range=heatmap.y_range,
        plot_height=400,
        plot_width=200,
    )
    echemplot.x_range.flipped = True
    echemplot.line(x=df_merged.voltage_V, y=df_merged.index)

    # link the y-scale of the single diffraction pattern plot to
    # the colorbar scale of the heatmap
    line_y_range = diffraction_line_plot.y_range
    line_y_range.js_link("start", color_mapper, "low")
    line_y_range.js_link("end", color_mapper, "high")

    # add linked crosshair between the heatmap and echem plot
    crosshair = CrosshairTool(dimensions="width", line_color="grey")
    heatmap.add_tools(crosshair)
    echemplot.add_tools(crosshair)

    # Double click on any plot to reset its zoom
    heatmap.js_on_event(DoubleTap, CustomJS(args=dict(p=heatmap), code="p.reset.emit()"))
    diffraction_line_plot.js_on_event(
        DoubleTap, CustomJS(args=dict(p=diffraction_line_plot), code="p.reset.emit()")
    )
    echemplot.js_on_event(DoubleTap, CustomJS(args=dict(p=echemplot), code="p.reset.emit()"))

    # create hover tool on both heatmap and echemplot that displays the hovered diffraction pattern
    hover = heatmap.select_one(HoverTool)
    hover.callback = CustomJS(
        args=dict(line_source=line_source, all_xrd_data=all_xrd_data),
        code="""
        const geometry = cb_data['geometry'];
        const index = Math.round(geometry.y);
        var data = line_source.data;
        console.log(all_xrd_data)
    
        data.intensity = all_xrd_data[index]
    
        line_source.change.emit();
        """,
    )
    hover.mode = "hline"
    echemplot.add_tools(hover)

    # set up a grid of the three plots and plot them
    grid = [[None, diffraction_line_plot], [echemplot, heatmap]]
    gp = gridplot(grid, merge_tools=True)  # , toolbar_options={"active_drag": "box_zoom"})
    if show_html:
        show(gp)

    save(gp)
