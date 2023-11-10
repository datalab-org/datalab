from typing import Dict, List, Optional, Sequence, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.events import DoubleTap
from bokeh.layouts import column, gridplot
from bokeh.models import (
    ColorBar,
    ColorMapper,
    CrosshairTool,
    CustomJS,
    HoverTool,
    LinearColorMapper,
)
from bokeh.models.widgets import Select
from bokeh.palettes import Accent, Dark2
from bokeh.plotting import ColumnDataSource, figure
from bokeh.themes import Theme
from scipy.signal import find_peaks

FONTSIZE = "12pt"
TYPEFACE = "Helvetica"  # "Lato"
COLORS = Dark2[8]
TOOLS = "box_zoom, reset, tap, crosshair, save"

SELECTABLE_CALLBACK_x = """
  var column = cb_obj.value;
  if (circle1) {circle1.glyph.x.field = column;}
  if (line1) {line1.glyph.x.field = column;}
  source.change.emit();
  xaxis.axis_label = column;
"""
SELECTABLE_CALLBACK_y = """
  var column = cb_obj.value;
  if (circle1) {circle1.glyph.y.field = column;}
  if (line1) {line1.glyph.y.field = column;}
  source.change.emit();
  yaxis.axis_label = column;
"""
SELECTABLE_CALLBACK_color = """
  var column = cb_obj.value;
  var low = Math.min.apply(Math, source.data[column]);
  var high = Math.max.apply(Math, source.data[column]);
  if (circle1) {circle1.glyph.line_color.field = column; circle1.glyph.fill_color.field = column;}
  if (line1) {line1.glyph.line_color.field = column;}
  if (colorbar) {colorbar.color_mapper.low = low; colorbar.color_mapper.high = high; colorbar.title = column;}
  source.change.emit();
"""


style = {
    "attrs": {
        # apply defaults to Figure properties
        "Figure": {
            "toolbar_location": "above",
            "outline_line_color": None,
            "min_border_right": 10,
        },
        "Title": {
            "text_font_size": FONTSIZE,
            "text_font_style": "bold",
            "text_font": TYPEFACE,
        },
        # apply defaults to Axis properties
        "Axis": {
            "axis_label_text_font": TYPEFACE,
            "axis_label_text_font_style": "normal",
            "axis_label_text_font_size": FONTSIZE,
            "major_tick_in": 0,
            "minor_tick_out": 0,
            "minor_tick_in": 0,
            "axis_line_color": "#CAC6B6",
            "major_tick_line_color": "#CAC6B6",
            "major_label_text_font_size": FONTSIZE,
            "axis_label_standoff": 15,
        },
        # apply defaults to Legend properties
        "Legend": {
            "background_fill_alpha": 0.8,
        },
    }
}

"""Additional style suitable for grid plots"""
grid_style = {
    "attrs": {
        # apply defaults to Figure properties
        "Figure": {
            "toolbar_location": "above",
            "outline_line_color": None,
            "min_border_right": 10,
        },
        "Title": {
            "text_font_style": "bold",
            "text_font": TYPEFACE,
        },
        # apply defaults to Axis properties
        "Axis": {
            "axis_label_text_font": TYPEFACE,
            "axis_label_text_font_style": "normal",
            "major_tick_in": 0,
            "minor_tick_out": 0,
            "minor_tick_in": 0,
            "axis_line_color": None,
            "major_tick_line_color": None,
            "minor_tick_line_color": None,
        },
        "Grid": {
            "grid_line_color": None,
        },
        # apply defaults to Legend properties
        "Legend": {
            "background_fill_alpha": 0.8,
        },
    }
}


mytheme = Theme(json=style)
grid_theme = Theme(json=grid_style)


def selectable_axes_plot(
    df: Union[Dict[str, pd.DataFrame], List[pd.DataFrame], pd.DataFrame],
    x_options: List[str],
    y_options: List[str],
    color_options: Optional[List[str]] = None,
    color_mapper: Optional[ColorMapper] = None,
    x_default: Optional[str] = None,
    y_default: Optional[Union[str, List[str]]] = None,
    label_x: bool = True,
    label_y: bool = True,
    plot_points: bool = True,
    point_size: int = 4,
    plot_line: bool = True,
    plot_image: bool = False,
    plot_title: Optional[str] = None,
    plot_index: Optional[int] = None,
    tools: Optional[List] = None,
    **kwargs,
):
    """
    Creates bokeh layout with selectable axis.

    Args:
        df: Dataframe, or list/dict of dataframes from data block.
        x_options: Selectable fields to use for the x-values
        y_options: Selectable fields to use for the y-values
        color_options: Selectable fields to colour lines/points by.
        color_mapper: Optional colour mapper to pass to switch between log and linear scales.
        x_default: Default x-axis that is plotted at start, defaults to first value of `x_options`
        y_default: Default y-axis that is plotted at start, defaults to first value of `y_options`.
            If provided a list, the first entry will be plotted as solid line, and all others will
            be transparent lines.
        plot_points: Whether to use plot markers.
        point_size: The size of markers, if enabled.
        plot_line: Whether to draw a line between points.
        plot_title: Global plot title to give to the figure.
        plot_index: If part of a larger number of plots, use this index for e.g., choosing the correct
            value in the colour cycle.
        tools: A list of Bokeh tools to enable.

    Returns:
        Bokeh layout
    """
    if not x_default:
        x_default = x_options[0]
    if not y_default:
        y_default = y_options[0]

    if isinstance(y_default, list):
        y_label = y_options[0]
    else:
        y_label = y_default

    x_axis_label = x_default if label_x else ""
    y_axis_label = y_label if label_y else ""

    p = figure(
        sizing_mode="scale_width",
        aspect_ratio=kwargs.pop("aspect_ratio", 1.5),
        match_aspect=kwargs.pop("match_aspect"),
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
        tools=TOOLS,
        title=plot_title,
        **kwargs,
    )

    if tools:
        p.add_tools(tools)

    if isinstance(df, pd.DataFrame):
        df = [df]

    callbacks_x = []
    callbacks_y = []
    callbacks_c = []

    if color_options:
        if color_mapper is None:
            color_mapper = LinearColorMapper(palette="Cividis256")

    hatch_patterns = [None, ".", "/", "x"]

    labels = []

    if isinstance(df, dict):
        labels = list(df.keys())

    for ind, df_ in enumerate(df):
        if isinstance(df, dict):
            df_ = df[df_]

        if labels:
            label = labels[ind]
        else:
            label = df_.index.name if len(df) > 1 else ""

        source = ColumnDataSource(df_)

        if color_options:
            color = {"field": color_options[0], "transform": color_mapper}
            line_color = "black"
            fill_color = None
            if hatch_patterns[ind % len(hatch_patterns)] is None:
                fill_color = color
        elif plot_index is not None:
            color = COLORS[plot_index % len(COLORS)]
            line_color = COLORS[plot_index % len(COLORS)]
            fill_color = COLORS[plot_index % len(COLORS)]
        else:
            color = COLORS[ind % len(COLORS)]
            line_color = COLORS[ind % len(COLORS)]
            fill_color = COLORS[ind % len(COLORS)]

        # If y_default is a list, plot the first one as a solid line, and the rest as transparent "auxiliary" lines
        y_aux = None
        if isinstance(y_default, list):
            if len(y_default) > 1:
                y_aux = y_default[1:]
            y_default = y_default[0]

        circles = (
            p.circle(
                x=x_default,
                y=y_default,
                source=source,
                size=point_size,
                line_color=color,
                fill_color=fill_color,
                legend_label=label,
                hatch_pattern=hatch_patterns[ind % len(hatch_patterns)],
                hatch_color=color,
            )
            if plot_points
            else None
        )

        lines = (
            p.line(x=x_default, y=y_default, source=source, color=line_color, legend_label=label)
            if plot_line
            else None
        )

        if y_aux:
            for y in y_aux:
                aux_lines = (  # noqa
                    p.line(
                        x=x_default,
                        y=y,
                        source=source,
                        color=color,
                        legend_label=label,
                        alpha=0.3,
                    )
                    if plot_line
                    else None
                )

        callbacks_x.append(
            CustomJS(
                args=dict(circle1=circles, line1=lines, source=source, xaxis=p.xaxis[0]),
                code=SELECTABLE_CALLBACK_x,
            )
        )
        callbacks_y.append(
            CustomJS(
                args=dict(circle1=circles, line1=lines, source=source, yaxis=p.yaxis[0]),
                code=SELECTABLE_CALLBACK_y,
            )
        )

    if color_mapper and color_options:
        colorbar = ColorBar(color_mapper=color_mapper, title=color_options[0])  # type: ignore
        p.add_layout(colorbar, "right")

        callbacks_c.append(
            CustomJS(
                args=dict(circle1=circles, line1=lines, source=source, colorbar=colorbar),
                code=SELECTABLE_CALLBACK_color,
            )
        )

    # Add list boxes for selecting which columns to plot on the x and y axis
    xaxis_select = Select(title="X axis:", value=x_default, options=x_options)
    xaxis_select.js_on_change("value", *callbacks_x)

    yaxis_select = Select(title="Y axis:", value=y_default, options=y_options)
    yaxis_select.js_on_change("value", *callbacks_y)

    color_select = Select(title="Colour by:", value=color_options[0], options=color_options)
    color_select.js_on_change("value", *callbacks_c)

    p.legend.click_policy = "hide"
    if len(df) <= 1:
        p.legend.visible = False

    plot_columns = [p]
    if len(x_options) > 1:
        plot_columns.append(xaxis_select)
    if len(y_options) > 1:
        plot_columns.append(yaxis_select)
    if len(color_options) > 1:
        plot_columns.append(color_select)

    layout = column(*plot_columns)

    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))
    return layout


def double_axes_echem_plot(
    df: pd.DataFrame,
    mode: Optional[str] = None,
    cycle_summary: pd.DataFrame = None,
    x_options: Sequence[str] = [],
    pick_peaks: bool = True,
    normalized: bool = False,
    **kwargs,
) -> gridplot:
    """Creates a Bokeh plot for electrochemistry data.

    Args:
        df: The pre-processed dataframe containing capacities and
            voltages, indexed by half cycle.
        mode: Either "dQ/dV", "dV/dQ", "normal" or None.
        x_options: Columns from `df` that can be selected for the
            first plot. The first will be used as the default.
        pick_peaks: Whether or not to pick and plot the peaks in dV/dQ mode.

    Returns: The Bokeh layout.
    """

    if not x_options:
        x_options = (
            ["capacity (mAh/g)", "voltage (V)", "time (s)", "current (mA/g)"]
            if normalized
            else ["capacity (mAh)", "voltage (V)", "time (s)", "current (mA)"]
        )

    x_options = [opt for opt in x_options if opt in df.columns]

    common_options = {"aspect_ratio": 1.5, "tools": TOOLS}
    common_options.update(**kwargs)

    if mode == "normal":
        mode = None

    modes = ("dQ/dV", "dV/dQ", "final capacity", None)
    if mode not in modes:
        raise RuntimeError(f"Mode must be one of {modes} not {mode}.")

    x_default = x_options[0]
    y_default = x_options[1]

    x_options = list(x_options)

    cmap = plt.get_cmap("inferno")

    plots = []
    # normal plot
    # x_label = "Capacity (mAh/g)" if x_default == "Capacity normalized" else x_default
    x_label = x_default
    p1 = figure(x_axis_label=x_label, y_axis_label="voltage (V)", **common_options)
    plots.append(p1)

    # the differential plot
    if mode in ("dQ/dV", "dV/dQ"):
        if mode == "dQ/dV":
            p2 = figure(
                x_axis_label=mode,
                y_axis_label="voltage (V)",
                y_range=p1.y_range,
                **common_options,
            )
        else:
            p2 = figure(
                x_axis_label=x_default, y_axis_label=mode, x_range=p1.x_range, **common_options
            )
        plots.append(p2)

    elif mode == "final capacity" and cycle_summary is not None:
        palette = Accent[3]

        p3 = figure(
            x_axis_label="Cycle number",
            y_axis_label="capacity (mAh/g)" if normalized else "capacity (mAh)",
            **common_options,
        )

        p3.line(
            x="full cycle",
            y="charge capacity (mAh/g)" if normalized else "charge capacity (mAh)",
            source=cycle_summary,
            legend_label="charge",
            line_width=2,
            color=palette[0],
        )
        p3.circle(
            x="full cycle",
            y="charge capacity (mAh/g)" if normalized else "charge capacity (mAh)",
            source=cycle_summary,
            fill_color="white",
            hatch_color=palette[0],
            legend_label="charge",
            line_width=2,
            size=12,
            color=palette[0],
        )
        p3.line(
            x="full cycle",
            y="discharge capacity (mAh/g)" if normalized else "discharge capacity (mAh)",
            source=cycle_summary,
            legend_label="discharge",
            line_width=2,
            color=palette[2],
        )
        p3.triangle(
            x="full cycle",
            y="discharge capacity (mAh/g)" if normalized else "discharge capacity (mAh)",
            source=cycle_summary,
            fill_color="white",
            hatch_color=palette[2],
            line_width=2,
            legend_label="discharge",
            size=12,
            color=palette[2],
        )

        p3.legend.location = "right"
        p3.y_range.start = 0

    lines = []
    grouped_by_half_cycle = df.groupby("half cycle")

    for ind, plot in enumerate(plots):
        x = x_default
        y = "voltage (V)"
        if ind == 1:
            if mode == "dQ/dV":
                x = "dQ/dV (mA/V)"
            else:
                y = "dV/dQ (V/mA)"

        # if filtering has removed all cycles, skip making the plot
        if len(df) < 1:
            raise RuntimeError("No data remaining to plot after filtering.")

        # trim the end of the colour cycle for visibility on a white background
        color_space = np.linspace(0.3, 0.7, max(int(df["half cycle"].max()), 1))  # type: ignore

        for _, group in grouped_by_half_cycle:
            line = plot.line(
                x=x,
                y=y,
                source=group,
                line_color=matplotlib.colors.rgb2hex(
                    cmap(color_space[int(group["half cycle"].max()) - 1])
                ),
                hover_line_width=2,
                selection_line_width=2,
                selection_line_color="black",
            )
            if mode == "dV/dQ" and ind == 1 and pick_peaks:
                # Check if half cycle or not
                dvdq_array = np.array(group[y])
                if group[y].mean() < 0:
                    dvdq_array *= -1

                peaks, _ = find_peaks(dvdq_array, prominence=5)
                peak_locs = group.iloc[peaks]
                p2.circle(x=x, y=y, source=peak_locs)

            if ind == 0:
                lines.append(line)

    # Only add the selectable axis to dQ/dV mode
    if mode in ("dQ/dV", None):
        callback_x = CustomJS(
            args=dict(lines=lines, xaxis=p1.xaxis[0]),
            code="""
                var column = cb_obj.value;
                console.log(column)
                for (let line of lines) {
                    line.glyph.x = { field: column };
                }
                xaxis.axis_label = column;
            """,
        )

        xaxis_select = Select(title="X axis:", value=x_default, options=x_options)
        xaxis_select.js_on_change("value", callback_x)

    if mode is None:
        callback_y = CustomJS(
            args=dict(lines=lines, yaxis=p1.yaxis[0]),
            code="""
                var column = cb_obj.value;
                console.log(column)
                for (let line of lines) {
                    line.glyph.y = { field: column };
                }
                yaxis.axis_label = column;
            """,
        )

        yaxis_select = Select(title="Y axis:", value=y_default, options=x_options)
        yaxis_select.js_on_change("value", callback_y)

    hovertooltips = [("Cycle No.", "@{full cycle}"), ("Half-cycle", "@{half cycle}")]

    if mode:
        crosshair = CrosshairTool(dimensions="width" if mode == "dQ/dV" else "height")
    for p in plots:
        if len(lines) < 100:
            p.add_tools(HoverTool(tooltips=hovertooltips))
        if mode:
            p.add_tools(crosshair)
        p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))

    if mode == "dQ/dV":
        grid = [[p1, p2], [xaxis_select]]
    elif mode == "dV/dQ":
        grid = [[p1], [p2]]
    elif mode == "final capacity":
        grid = [[p3]]
    else:
        grid = [[p1], [xaxis_select], [yaxis_select]]

    return gridplot(grid, sizing_mode="scale_width", toolbar_location="below")
