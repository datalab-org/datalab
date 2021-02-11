import pandas as pd
from bokeh.plotting import figure, ColumnDataSource, show
from bokeh.themes import built_in_themes, Theme
from bokeh.io import curdoc

from bokeh.events import DoubleTap
from bokeh.models.callbacks import CustomJS


FONTSIZE="14pt"
TYPEFACE = "Helvetica" # "Lato"
#SIZES = list(range(6, 22, 3))
#COLORS = Plasma256
TOOLS="box_zoom, reset, tap" # "hover"

style = {'attrs': {

    # apply defaults to Figure properties
    'Figure': {
        'toolbar_location': "above",
        'outline_line_color': None,
        'min_border_right': 10,
    },
    'Title': {
    'text_font_size':FONTSIZE,
    'text_font_style':'bold',
    'text_font': TYPEFACE,
    },

    # apply defaults to Axis properties
    'Axis': {
        'axis_label_text_font': TYPEFACE,
        'axis_label_text_font_style':'normal',
        'axis_label_text_font_size': FONTSIZE,
        'major_tick_in': None,
        'minor_tick_out': None,
        'minor_tick_in': None,
        'axis_line_color': '#CAC6B6',
        'major_tick_line_color': '#CAC6B6',
        'major_label_text_font_size': FONTSIZE,
        'axis_label_standoff':15
    },

     # apply defaults to Legend properties
    'Legend': {
        'background_fill_alpha': 0.8,
    }
}}


mytheme = Theme(json=style)

def simple_bokeh_plot(xy_filename="example_data/NaCoO2.xrdml.xy", x_label=None, y_label=None):

   df = pd.read_csv(xy_filename, sep='\s+', names=["twotheta", "intensity"])
   source = ColumnDataSource(df)

   kw = dict()
   p = figure(sizing_mode="scale_width",aspect_ratio=1.5, tools=TOOLS, **kw)

   p.xaxis.axis_label = x_label
   p.yaxis.axis_label = y_label


   # apply a theme. for some reason, this isn't carrying over 
   # to components() calls, so use components(theme=mytheme)
   curdoc().theme = mytheme 


   p.circle("twotheta", "intensity", source=source)
   p.toolbar.logo = "grey"
   p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code='p.reset.emit()'))
   # show(p)
   return p

if __name__ == "__main__":
   simple_bokeh_plot()

