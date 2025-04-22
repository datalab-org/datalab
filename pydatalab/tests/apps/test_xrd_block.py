from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import XRDBlock
from pydatalab.bokeh_plots import selectable_axes_plot

XRD_DATA_FILES = list((Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*"))


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
        df, y_options = XRDBlock.load_pattern(f)
        assert all(y in df.columns for y in y_options)


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_plot(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
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
