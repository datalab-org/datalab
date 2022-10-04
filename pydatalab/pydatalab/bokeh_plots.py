from typing import List, Optional, Sequence, Union

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.events import DoubleTap
from bokeh.layouts import column, gridplot
from bokeh.models import CrosshairTool, CustomJS, HoverTool
from bokeh.models.widgets import Select
from bokeh.palettes import Dark2
from bokeh.plotting import ColumnDataSource, figure
from bokeh.themes import Theme
from scipy.signal import find_peaks

FONTSIZE = "12pt"
TYPEFACE = "Helvetica"  # "Lato"
# SIZES = list(range(6, 22, 3))
# COLORS = Plasma256
COLORS = Dark2[8]
TOOLS = "box_zoom, reset, tap, crosshair"

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


mytheme = Theme(json=style)


def selectable_axes_plot(
    df: Union[List[pd.DataFrame], pd.DataFrame],
    x_options: List[str],
    y_options: List[str],
    x_default: Optional[str] = None,
    y_default: Optional[str] = None,
    plot_points: bool = True,
    point_size: int = 4,
    plot_line: bool = True,
    tools: Union[str, List[str]] = TOOLS,
    **kwargs,
):
    """
    Creates bokeh layout with selectable axis.

    Args:
        df: Dataframe, or list of dataframes from data block.
        x_options: Selectable fields to use for the x-values
        y_options: Selectable fields to use for the y-values
        x_default: Default x-axis that is printed at start, defaults to first value of `x_options`
        y_default: Default y-axis that is printed at start, defaults to first value of `y_options`.
        plot_points: Whether to use plot markers.
        point_size: The size of markers, if enabled.
        plot_line: Whether to draw a line between points.
        tools: A list of Bokeh tools to enable.

    Returns:
        Bokeh layout
    """
    if not x_default:
        x_default = x_options[0]
        y_default = y_options[0]

    p = figure(
        sizing_mode="scale_width",
        aspect_ratio=1.5,
        x_axis_label=x_default,
        y_axis_label=y_default,
        tools=tools,
        **kwargs,
    )

    if isinstance(df, pd.DataFrame):
        df = [df]

    callbacks_x = []
    callbacks_y = []
    for ind, df_ in enumerate(df):
        source = ColumnDataSource(df_)

        label = df_.index.name if len(df) > 1 else ""

        circles = (
            p.circle(x=x_default, y=y_default, source=source, size=point_size, color=COLORS[ind])
            if plot_points
            else None
        )
        lines = (
            p.line(x=x_default, y=y_default, source=source, color=COLORS[ind], legend_label=label)
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

    # Add list boxes for selecting which columns to plot on the x and y axis
    xaxis_select = Select(title="X axis:", value=x_default, options=x_options)
    xaxis_select.js_on_change("value", *callbacks_x)

    yaxis_select = Select(title="Y axis:", value=y_default, options=y_options)
    yaxis_select.js_on_change("value", *callbacks_y)

    p.legend.click_policy = "hide"
    if len(df) <= 1:
        p.legend.visible = False

    layout = column(p, xaxis_select, yaxis_select)

    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))
    return layout


def double_axes_echem_plot(
    df: pd.DataFrame,
    mode: Optional[str] = None,
    x_options: Sequence[str] = ("Capacity", "Voltage", "Time", "Current"),
    pick_peaks: bool = True,
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

    common_options = {"aspect_ratio": 1.5, "tools": TOOLS}
    common_options.update(**kwargs)

    if mode == "normal":
        mode = None

    modes = ("dQ/dV", "dV/dQ", None)
    if mode not in modes:
        raise RuntimeError(f"Mode must be one of {modes} not {mode}.")

    x_default = x_options[0]
    y_default = x_options[1]

    x_options = list(x_options)

    cmap = plt.get_cmap("inferno")

    plots = []
    # normal plot
    p1 = figure(x_axis_label=x_default, y_axis_label="Voltage (V)", **common_options)
    plots.append(p1)

    # the differential plot
    if mode:
        if mode == "dQ/dV":
            p2 = figure(
                x_axis_label=mode,
                y_axis_label="Voltage (V)",
                y_range=p1.y_range,
                **common_options,
            )
        else:
            p2 = figure(
                x_axis_label=x_default, y_axis_label=mode, x_range=p1.x_range, **common_options
            )
        plots.append(p2)

    lines = []
    grouped_by_half_cycle = df.groupby("half cycle")
    max_full_cycle = df["full cycle"].max()

    for ind, plot in enumerate(plots):
        x = x_default
        y = "Voltage"
        if ind == 1:
            if mode == "dQ/dV":
                x = "dqdv"
            else:
                y = "dvdq"

        for _, group in grouped_by_half_cycle:
            # trim the end of the colour cycle for visibility on a white background
            if max_full_cycle <= 1:
                color_value = 0.5
            else:
                color_value = 0.8 * max(
                    0.0, (group["full cycle"].iloc[0] - 1) / (max_full_cycle - 1)
                )

            line = plot.line(
                x=x,
                y=y,
                source=group,
                line_color=matplotlib.colors.rgb2hex(cmap(color_value)),
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
        p.add_tools(HoverTool(tooltips=hovertooltips))
        if mode:
            p.add_tools(crosshair)
        p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))

    if mode == "dQ/dV":
        grid = [[p1, p2], [xaxis_select]]
    elif mode == "dV/dQ":
        # grid = [[p1, p2]]
        grid = [[p1], [p2]]
    else:
        grid = [[p1], [xaxis_select], [yaxis_select]]

    return gridplot(grid, sizing_mode="scale_width", toolbar_location="below")
