import pandas as pd
from bokeh.layouts import column
from bokeh.models import CustomJS, Slider
from bokeh.plotting import ColumnDataSource, figure, show

df = pd.DataFrame([[1, 2, 3, 4, 5], [2, 20, 3, 10, 20]], columns=["1", "21", "22", "31", "32"])
source_available = ColumnDataSource(df)
source_visible = ColumnDataSource(data=dict(x=df["1"], y=df["21"]))

p = figure(title="SLIMe")
p.circle("x", "y", source=source_visible)

slider1 = Slider(title="SlideME", value=2, start=2, end=3, step=1)
slider2 = Slider(title="SlideME2", value=1, start=1, end=2, step=1)

slider1.js_on_change(
    "value",
    CustomJS(
        args=dict(
            source_visible=source_visible,
            source_available=source_available,
            slider1=slider1,
            slider2=slider2,
        ),
        code="""
        var sli1 = slider1.value;
        var sli2 = slider2.value;
        var data_visible = source_visible.data;
        var data_available = source_available.data;
        data_visible.y = data_available[sli1.toString() + sli2.toString()];
        source_visible.change.emit();
    """,
    ),
)
slider2.js_on_change(
    "value",
    CustomJS(
        args=dict(
            source_visible=source_visible,
            source_available=source_available,
            slider1=slider1,
            slider2=slider2,
        ),
        code="""
        var sli1 = slider1.value;
        var sli2 = slider2.value;
        var data_visible = source_visible.data;
        var data_available = source_available.data;
        data_visible.y = data_available[sli1.toString() + sli2.toString()];
        source_visible.change.emit();
    """,
    ),
)


show(column(p, slider1, slider2))
