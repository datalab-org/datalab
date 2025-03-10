from pathlib import Path

import pytest

from pydatalab.apps.ftir import FTIRBlock, parse_ftir_asp
from bokeh.models import HoverTool, LogColorMapper
from pydatalab.bokeh_plots import selectable_axes_plot


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "FTIR").glob("*")


def test_load(data_files):
    for f in data_files:
        df = parse_ftir_asp(f)
        assert len(df) == 1932
        assert all(x in df.columns for x in ["Wavenumber", "Absorbance"])
        assert df["Wavenumber"].min() == 400.688817501068
        assert df["Wavenumber"].max() == 3999.43349933624
        assert df["Absorbance"].argmin() == 987
        assert df["Absorbance"].argmax() == 1928
        # Checking height of peak at 1079 cm-1 has correct height
        mask = (df["Wavenumber / cm-1"] > 800) & (df["Wavenumber / cm-1"] < 1500)
        assert max(df["Absorbance"][mask]) == 0.0536771319493808

def test_plot(data_files):
    f = next(data_files)
    ftir_data = FTIRBlock.parse_ftir_asp(f)
    layout = selectable_axes_plot(
                ftir_data,
                x_options=["Wavenumber"],
                y_options=["Absorbance"],
                x_range=(ftir_data["Wavenumber"].max() + 50,
                          ftir_data["Wavenumber"].min() - 50),
                # color_options=["Frequency [Hz]"],
                color_mapper=LogColorMapper("Cividis256"),
                plot_points=False,
                plot_line=True,
                tools=HoverTool(
                    tooltips=[("Wavenumber / cm\u207B\u00B9", "@Wavenumber{0.00}"), 
                              ("Absorbance", "@Absorbance{0.0000}")],  # Display x and y values to specified decimal places
                    mode='vline'  # Ensures hover follows the x-axis
                    ),
            )
    assert layout
