from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import XRDBlock

XRD_DATA_FILES = list((Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*"))


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
        df, y_options, metadata = XRDBlock.load_pattern(f)
        assert all(y in df.columns for y in y_options)


def test_event():
    block = XRDBlock(item_id="test-id")
    assert block.data["wavelength"] == 1.54060
    block.process_events({"event_name": "set_wavelength", "wavelength": 1.0})
    assert block.data["wavelength"] == 1.0
    block.process_events({"event_name": "set_wavelength", "wavelength": None})
    assert block.data["wavelength"] == 1.54060
    block.process_events({"event_name": "set_wavelength", "wavelength": -1.0})
    assert len(block.data["errors"]) == 1
    assert block.data["wavelength"] == 1.54060


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_single_plots(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
        block = XRDBlock(item_id="test")
        block.generate_xrd_plot(f)
        assert block.data["bokeh_plot_data"]
