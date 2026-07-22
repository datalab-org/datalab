from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import XRDBlock

XRD_DATA_FILES = list((Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*"))


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    pipeline = XRDBlock.pipeline.clone()
    pipeline.set_caching_for_entire_pipeline(False)
    if f.suffix in XRDBlock.accepted_file_extensions:
        _, dfs = pipeline.parser_pass_step(["Null"], None, [f])
        dfs = pipeline.processor_pass_step(
            data={"wavelength": 1.5},
            file_folder="",
            parser_checksums=["Null"],
            parser_output_df=dfs,
        )
        df = dfs[0]
        assert all(y in df.columns for y in df.attrs["y_options"])


def test_event():
    block = XRDBlock(item_id="test-id")
    assert block.data["wavelength"] == 1.54060
    block.process_events({"event_name": "set_wavelength", "wavelength": 1.0})
    assert block.data["wavelength"] == 1.0
    block.process_events({"event_name": "set_wavelength", "wavelength": None})
    assert block.data["wavelength"] == 1.0
    block.process_events({"event_name": "set_wavelength", "wavelength": -1.0})
    assert len(block.data["errors"]) == 1
    assert block.data["wavelength"] == 1.0


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_single_plots(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
        block = XRDBlock(item_id="test")
        block.pipeline.set_caching_for_entire_pipeline(False)
        result = block.pipeline.perform_entire_pipeline(
            data=block.data,
            file_folder="",
            files=[f],
            checksums=["None"],
        )
        assert result["bokeh_plot_data"]
