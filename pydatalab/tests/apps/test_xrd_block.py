from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import xrd_block
from pydatalab.pipeline_block.block_manager import PipelineBlockManager

XRD_DATA_FILES = list((Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*"))


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    pipeline = xrd_block["pipeline"].clone()
    pipeline.set_caching_for_entire_pipeline(False)
    if f.suffix in xrd_block["default_params"].accepted_file_extensions:
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
    block_manager = PipelineBlockManager()
    block_manager.register_block(**xrd_block)
    block_data = block_manager.create_block_data("xrd", item_id="1")
    assert block_data["wavelength"] == 1.54060
    block_manager.process_events(block_data, {"event_name": "set_wavelength", "wavelength": 1.0})
    assert block_data["wavelength"] == 1.0
    block_manager.process_events(block_data, {"event_name": "set_wavelength", "wavelength": None})
    assert block_data["wavelength"] == 1.0
    block_manager.process_events(block_data, {"event_name": "set_wavelength", "wavelength": -1.0})
    assert len(block_data["errors"]) == 1
    assert block_data["wavelength"] == 1.0


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_single_plots(f):
    block_manager = PipelineBlockManager()
    block_manager.register_block(**xrd_block)

    if f.suffix in block_manager._list_of_blocks["xrd"].accepted_file_extensions:
        block_data = block_manager.create_block_data("xrd", item_id="test")

        pipeline = block_manager._list_of_pipelines["xrd"]
        pipeline.set_caching_for_entire_pipeline(False)

        result = pipeline.perform_entire_pipeline(
            data=block_data,
            file_folder="",
            files=[f],
            checksums=["None"],
        )
        assert result["bokeh_plot_data"]
