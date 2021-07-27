import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from bokeh.events import DoubleTap
from bokeh.layouts import column, gridplot
from bokeh.models import CustomJS, HoverTool
from bokeh.models.widgets import Select
from bokeh.plotting import ColumnDataSource, figure
from bokeh.themes import Theme
from scipy.signal import find_peaks
from bokeh.models import CrosshairTool

FONTSIZE = "14pt"
TYPEFACE = "Helvetica"  # "Lato"
# SIZES = list(range(6, 22, 3))
# COLORS = Plasma256
TOOLS = "box_zoom, reset, tap"  # "hover"

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
            "major_tick_in": None,
            "minor_tick_out": None,
            "minor_tick_in": None,
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


def selectable_axes_plot(df, x_options, y_options, x_default=None, y_default=None, **kwargs):
    """
    Creates bokeh layout with selectable axis.

    Args:
        df: Input df from echem_block.py
        x_options: Selectable x-axis options
        y_options: Selectable y-axis options
        x_default: Default x-axis that is printed at start, None specified means first value in x_options list will be chosen
        y_default: Default y-axis that is printed at start, None specified means first value in y_options list will be chosen

    Returns:
        Bokeh layout
    """
    source = ColumnDataSource(df)

    if not x_default:
        x_default = x_options[0]
        y_default = y_options[0]

    # colormapper = LinearColorMapper(palette="Plasma256",low=df['colour'].min(), high=df['colour'].max())

    code_x = """
      var column = cb_obj.value;
      circle1.glyph.x.field = column;
      source.change.emit();
      xaxis.axis_label = column;
      """
    code_y = """
      var column = cb_obj.value;
      circle1.glyph.y.field = column;
      source.change.emit();
      yaxis.axis_label = column;
      """

    p = figure(
        sizing_mode="scale_width",
        aspect_ratio=1.5,
        x_axis_label=x_default,
        y_axis_label=y_default,
        tools=TOOLS,
        **kwargs
    )

    circle1 = p.circle(x=x_default, y=y_default, source=source)

    callback_x = CustomJS(args=dict(circle1=circle1, source=source, xaxis=p.xaxis[0]), code=code_x)
    callback_y = CustomJS(args=dict(circle1=circle1, source=source, yaxis=p.yaxis[0]), code=code_y)

    # Add list boxes for selecting which columns to plot on the x and y axis
    xaxis_select = Select(title="X axis:", value=x_default, options=x_options)
    xaxis_select.js_on_change("value", callback_x)

    yaxis_select = Select(title="Y axis:", value=y_default, options=y_options)
    yaxis_select.js_on_change("value", callback_y)

    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))
    layout = column(p, xaxis_select, yaxis_select)
    return layout


def selectable_axes_plot_colours(
    df, x_options, y_options, x_default="Capacity", y_default="Voltage", **kwargs
):
    """
    Creates bokeh layout with selectable axis.

    Args:
        df: Input df from echem_block.py
        x_options: Selectable x-axis options
        y_options: Selectable y-axis options
        x_default: Default x-axis that is printed at start, Default set to Capacity
        y_default: Default y-axis that is printed at start, Default set to Voltage

    Returns:
        Bokeh layout
    """
    source = ColumnDataSource(df)

    if not x_default:
        x_default = x_options[0]
        y_default = y_options[0]

    p = figure(
        sizing_mode="scale_width",
        aspect_ratio=1.5,
        x_axis_label=x_default,
        y_axis_label=y_default,
        tools=TOOLS,
        **kwargs
    )

    # Need to group the df into groups of different half cycles and then plot a line through it. Plotting groups of full cycles means the point will
    # jump from one end to the other when charge --> discharge

    grouped_by_halfcycle = df.groupby("half cycle")

    # We need to colour lines by full-cycles in a gradient
    cmap = plt.get_cmap("plasma")
    full_cycle_group = df["full cycle"].unique()
    myList = sorted(full_cycle_group)
    length = len(myList)
    numberList = np.linspace(0, 1, length)
    # Since we are plotting by half cycle, colour is assigned by half cycle, even though we need full cycle
    # to get around this, we will assign each pair of half cycle for each full cycle the same cmap value
    newList = []
    for i in numberList:
        newList.extend([i, i])

    counter = 0
    lines = []
    for name, group in grouped_by_halfcycle:
        group = group.copy()
        val = newList[counter]
        line = p.line(
            x=x_default,
            y=y_default,
            source=group,
            line_color=matplotlib.colors.rgb2hex(cmap(val)),
        )
        lines.append(line)
        counter = counter + 1

    callback_x = CustomJS(
        args=dict(lines=lines, xaxis=p.xaxis[0]),
        code="""
            var column = cb_obj.value;
            console.log(column)
            for (let line of lines) {
                line.glyph.x = { field: column };
            }
            xaxis.axis_label = column;
        """,
    )
    callback_y = CustomJS(
        args=dict(lines=lines, yaxis=p.yaxis[0]),
        code="""
            var column = cb_obj.value;
            console.log(column)
            for (let line of lines) {
                line.glyph.y = { field: column };
            }
            yaxis.axis_label = column;
        """,
    )

    # Add list boxes for selecting which columns to plot on the x and y axis
    xaxis_select = Select(title="X axis:", value=x_default, options=x_options)
    xaxis_select.js_on_change("value", callback_x)

    yaxis_select = Select(title="Y axis:", value=y_default, options=y_options)
    yaxis_select.js_on_change("value", callback_y)

    # hover = p.select(type=HoverTool)
    hovertooltips = [
        ("Cycle No.", "@{full cycle}"),
    ]

    p.add_tools(HoverTool(tooltips=hovertooltips))

    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))
    layout = column(p, xaxis_select, yaxis_select)
    return layout


def double_axes_plot(df, df2, x_options=["Capacity", "Time"], x_default="Capacity", **kwargs):
    """
    Creates bokeh layout with 2 plots - one is normal, one is dq/dv

    Args:
        df: Input df from echem_block.py to be used for first, normal plot
        df2: Input df from echem_block.py with dq/dv values for second plot
        x_options: Selectable x-axis options
        y_options: Selectable y-axis options
        x_default: Default x-axis that is printed at start, Default set to Capacity


    Returns:
        Bokeh layout
    """
    source1 = ColumnDataSource(df)
    source2 = ColumnDataSource(df2)

    # normal plot
    p1 = figure(
        aspect_ratio=1.5, x_axis_label=x_default, y_axis_label="Voltage", tools=TOOLS, **kwargs
    )
    # circle1 = p1.circle(x='Capacity', y=y_default, source=source1 )

    # Need to group the df into groups of different half cycles and then plot a line through it. Plotting groups of full cycles means the point will
    # jump from one end to the other when charge --> discharge

    half_cycle_group = df.groupby("half cycle")

    # We need to colour lines by full-cycles in a gradient
    cmap = plt.get_cmap("plasma")
    full_cycle_group = df["full cycle"].unique()
    myList = sorted(full_cycle_group)
    length = len(myList)
    numberList = np.linspace(0, 1, length)
    # Since we are plotting by half cycle, colour is assigned by half cycle, even though we need full cycle
    # to get around this, we will assign each pair of half cycle for each full cycle the same cmap value
    newList = []
    for i in numberList:
        newList.extend([i, i])

    counter = 0
    lines = []
    for name, group in half_cycle_group:
        val = newList[counter]
        line = p1.line(
            x=x_default,
            y="Voltage",
            source=group,
            line_color=matplotlib.colors.rgb2hex(cmap(val)),
        )
        lines.append(line)
        counter = counter + 1

    # dqdv plot
    p2 = figure(
        aspect_ratio=1.5,
        x_axis_label='dq/dv',
        y_axis_label="Voltage",
        tools=TOOLS,
        y_range=p1.y_range,
        **kwargs
    )

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

    # circle2 = p2.circle(x='dqdv', y=y_default, source=source2)

    grouped2 = df2.groupby("half cycle")

    counter2 = 0
    # print(len(grouped))
    for name, group in grouped2:
        val2 = newList[counter2]
        circle2 = p2.line(
            x="dqdv",
            y="Voltage",
            source=group,
            line_color=matplotlib.colors.rgb2hex(cmap(val2)),
        )
        counter2 = counter2 + 1

    # hover = p.select(type=HoverTool)
    hovertooltips = [
        ("Cycle No.", "@{full cycle}"),
        ("Half-cycle", "@{half cycle}")
    ]

    p1.add_tools(HoverTool(tooltips=hovertooltips))
    p2.add_tools(HoverTool(tooltips=hovertooltips))

    crosshair = CrosshairTool(dimensions="width")
    p1.add_tools(HoverTool(tooltips=hovertooltips))
    p2.add_tools(HoverTool(tooltips=hovertooltips))
    p1.add_tools(crosshair)
    p2.add_tools(crosshair)

    p1.js_on_event(DoubleTap, CustomJS(args=dict(p=p1), code="p.reset.emit()"))
    p2.js_on_event(DoubleTap, CustomJS(args=dict(p=p2), code="p.reset.emit()"))
    layout = gridplot(
        [[p1, p2], [xaxis_select]], sizing_mode="scale_width", toolbar_location="below"
    )
    return layout


def double_axes_plot_dvdq(df, dvdq_df, x_default="Capacity", **kwargs):
    """
    Creates bokeh layout with 2 plots - one is normal, one is dq/dv

    Args:
        df: Input df from echem_block.py to be used for first, normal plot
        dvdq_df: Input df from echem_block.py with dv/dq values for second plot
        x_default: Default x-axis that is printed at start, Default set to Capacity


    Returns:
        Bokeh layout
    """
    source1 = ColumnDataSource(df)
    source2 = ColumnDataSource(dvdq_df)

    # colormapper = LinearColorMapper(palette="Plasma256",low=df['colour'].min(), high=df['colour'].max())

    code_x = """
      var column = cb_obj.value;
      circle1.glyph.x.field = column;
      source.change.emit();
      xaxis.axis_label = column;
      """
    code_y = """
      var column = cb_obj.value;
      circle1.glyph.y.field = column;
      source.change.emit();
      yaxis.axis_label = column;
      """

    # normal plot
    p1 = figure(
        aspect_ratio=1.5, x_axis_label=x_default, y_axis_label="Voltage", tools=TOOLS, **kwargs
    )
    # circle1 = p1.circle(x='Capacity', y=y_default, source=source1 )

    # Need to group the df into groups of different half cycles and then plot a line through it. Plotting groups of full cycles means the point will
    # jump from one end to the other when charge --> discharge

    half_cycle_group = df.groupby("half cycle")

    # We need to colour lines by full-cycles in a gradient
    cmap = plt.get_cmap("plasma")
    full_cycle_group = df["full cycle"].unique()
    myList = sorted(full_cycle_group)
    length = len(myList)
    numberList = np.linspace(0, 1, length)
    # Since we are plotting by half cycle, colour is assigned by half cycle, even though we need full cycle
    # to get around this, we will assign each pair of half cycle for each full cycle the same cmap value
    newList = []
    for i in numberList:
        newList.extend([i, i])

    counter = 0
    for name, group in half_cycle_group:
        val = newList[counter]
        circle1 = p1.line(
            x=x_default,
            y="Voltage",
            source=group,
            line_color=matplotlib.colors.rgb2hex(cmap(val)),
        )
        counter = counter + 1

    # dvdq plot
    p2 = figure(
        aspect_ratio=1.5,
        x_axis_label=x_default,
        y_axis_label="dv/dq",
        tools=TOOLS,
        x_range=p1.x_range,
        **kwargs
    )
    # circle2 = p2.circle(x='dqdv', y=y_default, source=source2)

    cmap = plt.get_cmap("plasma")

    grouped2 = dvdq_df.groupby("half cycle")

    counter2 = 0
    # print(len(grouped))
    for name, group in grouped2:
        val2 = newList[counter2]
        circle2 = p2.line(
            x="Voltage",
            y="dqdv",
            source=group,
            line_color=matplotlib.colors.rgb2hex(cmap(val2)),
        )
        counter2 = counter2 + 1

        # Check if half cycle or not
        if group["dqdv"].mean() > 0:
            my_dqdv_array = np.array(group["dqdv"])

            peaks, _ = find_peaks(my_dqdv_array, prominence=5)

            my_peaks_df = group.iloc[peaks]

            circle3 = p2.circle(x="Voltage", y="dqdv", source=my_peaks_df)
        else:
            my_dqdv_array = np.array(-group["dqdv"])

            peaks, _ = find_peaks(my_dqdv_array, prominence=5)

            my_peaks_df = group.iloc[peaks]

            circle3 = p2.circle(x="Voltage", y="dqdv", source=my_peaks_df)

    # hover = p.select(type=HoverTool)
    hovertooltips = [
        ("Cycle No.", "@{full cycle}"),
        ("Half-cycle", "@{half cycle}")
    ]

    crosshair = CrosshairTool(dimensions="height")
    p1.add_tools(HoverTool(tooltips=hovertooltips))
    p2.add_tools(HoverTool(tooltips=hovertooltips))
    p1.add_tools(crosshair)
    p2.add_tools(crosshair)
    p1.js_on_event(DoubleTap, CustomJS(args=dict(p=p1), code="p.reset.emit()"))
    p2.js_on_event(DoubleTap, CustomJS(args=dict(p=p2), code="p.reset.emit()"))
    layout = gridplot([[p1, p2]], sizing_mode="scale_width", toolbar_location="below")
    return layout
