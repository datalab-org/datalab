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
from bokeh.plotting import figure, show
from neware_reader.neware import nda_to_csv, read_nda

STARTING_INTENSITY_MAX = 35000
TOOLS = "box_zoom, reset, tap"


# read in log file
log_filename = "log_operando_cell6_jdb11-4_e1_xs3_NaCoO2_run1.csv"
df_log = pd.read_csv(
    log_filename,
    sep=", ",
    skiprows=1,
    names=["scan_number", "cell_name", "xrd_timestamp"],
    parse_dates=["xrd_timestamp"],
    engine="python",
)

# read in echem data
timedelta = datetime.timedelta(hours=1)  # account for difference in time settings between computers
echem_filename = "jdb11-4_e1_xs3_NaCoO2_DLS_cell6_127.0.0.1_240016-1-6-2818573730.nda"
df_echem = read_nda(echem_filename)
df_echem["timestamp"] = pd.to_datetime(df_echem["timestamp"]) - timedelta
df_echem = df_echem.rename(columns={"timestamp": "echem_timestamp"})

time_deltas = df_echem.echem_timestamp - df_echem.echem_timestamp.iloc[0]
df_echem["elapsed_time_hours"] = [delta.total_seconds() / 3600 for delta in time_deltas]

# Merge the two tables via closest timestamp (results in 1 line for every line in xrd log file)
df_merged = pd.merge_asof(
    df_log, df_echem, left_on="xrd_timestamp", right_on="echem_timestamp", direction="nearest"
)

# get the files
base = "/Users/josh/Dropbox/Diamond_operando_13May22/all_data/jdb11-4_e1_xs3_NaCoO2/"
dfs = []
for i, scan_number in enumerate(df_merged.scan_number):
    fn = j(base, f"{scan_number}-mythen_summed.dat")
    df = pd.read_csv(fn, comment="'", sep=r"\s+", names=["twotheta", "intensity", "error"])
    df["pattern_index"] = i
    dfs.append(df)

# if no log file, can list files and sort by run number
# fns = glob.glob(
# "/Users/josh/Dropbox/Diamond_operando_13May22/all_data/jdb11-4_e1_xs3_NaCoO2/*-mythen_summed.dat"
# )
# fns = sorted(fns, key=lambda x: int(re.search(r"(\d+)-mythen_summed.dat", x).group(1)))

# read in all files to dataframes
# dfs = []
# for i, fn in enumerate(fns):
#     df = pd.read_csv(fn, comment="'", sep=r"\s+", names=["twotheta", "intensity", "error"])
#     df["pattern_index"] = i

#     dfs.append(df)

all_data = np.zeros((len(dfs), len(df)))
for i, df in enumerate(dfs):
    all_data[i] = df["intensity"]


# using griddata for interpolation
# combined_df =  pd.concat(dfs)

# x = combined_df.twotheta
# y = combined_df.pattern_index
# z = combined_df.intensity

# grid_x, grid_y = np.mgrid[x.min():x.max():1000j, y.min():y.max():1000j]

# cubic = True
# grid = griddata((x,y),z, (grid_x, grid_y), method="cubic" if cubic else "linear")

heatmap = figure(
    x_axis_label="2theta",
    tooltips=[("x", "$x"), ("y", "$y"), ("value", "@image")],
    active_drag="box_zoom",
    # aspect_ratio=1.5,
    plot_height=400,
    # plot_width=300,
)
heatmap.x_range.range_padding = heatmap.y_range.range_padding = 0

cutoff_index = 5000
all_data = all_data[:, :cutoff_index]
twotheta = df["twotheta"].iloc[:cutoff_index]

color_mapper = LinearColorMapper(high=STARTING_INTENSITY_MAX, low=0, palette="Viridis256")

# # must give a vector of image data for image parameter
img = heatmap.image(
    image=[all_data[:, :cutoff_index]],
    x=twotheta.min(),
    y=0,
    dw=twotheta.max() - twotheta.min(),
    dh=len(dfs),
    # palette="Viridis256",
    color_mapper=color_mapper,
    level="image",
)

heatmap.grid.grid_line_width = 0
# reset zoom on doubleclick


lineplot = figure(
    # x_axis_label="2theta",
    y_axis_label="intensity",
    aspect_ratio=2,
    x_range=heatmap.x_range,
    y_range=(0, STARTING_INTENSITY_MAX),
)
line_source = ColumnDataSource(dfs[0][:cutoff_index])
line1 = lineplot.line(x="twotheta", y="intensity", source=line_source)

echemplot = figure(
    x_axis_label="voltage (V)",
    y_axis_label="pattern index",
    y_range=heatmap.y_range,
    plot_height=400,
    plot_width=200,
)

echemplot.line(x=df_merged.voltage_V, y=df_merged.index)

crosshair = CrosshairTool(dimensions="width", line_color="grey")
heatmap.add_tools(crosshair)

grid = [[None, lineplot], [echemplot, heatmap]]


hover = heatmap.select_one(HoverTool)
hover.callback = CustomJS(
    args=dict(line_source=line_source, all_data=all_data),
    code="""
    const geometry = cb_data['geometry'];
    const index = Math.round(geometry.y);
    var data = line_source.data;
    console.log(all_data)
    data.intensity = all_data[index]
    line_source.change.emit();
    """,
)

grid = [[None, lineplot], [echemplot, heatmap]]
gp = gridplot(grid, merge_tools=True)  # , toolbar_options={"active_drag": "box_zoom"})


echemplot.add_tools(crosshair, hover)

heatmap.js_on_event(DoubleTap, CustomJS(args=dict(p=heatmap), code="p.reset.emit()"))
lineplot.js_on_event(DoubleTap, CustomJS(args=dict(p=lineplot), code="p.reset.emit()"))
echemplot.js_on_event(DoubleTap, CustomJS(args=dict(p=echemplot), code="p.reset.emit()"))


color_bar = ColorBar(color_mapper=color_mapper)  # , label_standoff=12)
line_y_range = lineplot.y_range
line_y_range.js_link("start", color_mapper, "low")
line_y_range.js_link("end", color_mapper, "high")
# color_mapper.js_link("high", line_y_range, "end")
heatmap.add_layout(color_bar, "right")

# gp.toolbar.active_drag = None

show(gp)
