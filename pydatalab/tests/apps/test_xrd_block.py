from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import XRDBlock
from pydatalab.bokeh_plots import selectable_axes_plot


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*")


def test_load(data_files):
    for f in data_files:
        df, y_options = XRDBlock.load_pattern(f)
        assert all(y in df.columns for y in y_options)


def test_plot(data_files):
    f = next(data_files)
    df, y_options = XRDBlock.load_pattern(f)
    p = selectable_axes_plot(
        [df],
        x_options=["2θ (°)", "Q (Å⁻¹)", "d (Å)"],
        y_options=y_options,
        plot_line=True,
        plot_points=True,
        point_size=3,
    )
    assert p
