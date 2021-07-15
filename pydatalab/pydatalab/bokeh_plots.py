import pandas as pd
from bokeh.plotting import figure, ColumnDataSource, show
from bokeh.themes import built_in_themes, Theme
from bokeh.io import curdoc

from bokeh.events import DoubleTap
from bokeh.models.callbacks import CustomJS


from bokeh.models.widgets import Select, TextInput
from bokeh.layouts import column


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


def simple_bokeh_plot(xy_filename, x_label=None, y_label=None):

    df = pd.read_csv(xy_filename, sep="\s+", names=["x_col", "y_col"])
    source = ColumnDataSource(df)
    # source = ColumnDataSource({'x_col': x, 'y_col': y})

    kw = dict()
    p = figure(sizing_mode="scale_width", aspect_ratio=1.5, tools=TOOLS, **kw)

    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label

    # apply a theme. for some reason, this isn't carrying over
    # to components() calls, so use components(theme=mytheme)
    curdoc().theme = mytheme

    p.circle("x_col", "y_col", source=source)
    p.toolbar.logo = "grey"
    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))
    # show(p)
    return p


def selectable_axes_plot(df, x_options, y_options, x_default=None, y_default=None, **kwargs):
    source = ColumnDataSource(df)

    if not x_default:
        x_default = x_options[0]
        y_default = y_options[0]

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


if __name__ == "__main__":
    simple_bokeh_plot()
