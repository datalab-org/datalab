from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import xrd_block
from pydatalab.pipeline_block.block_manager import PipelineBlockManager
from pydatalab.pipeline_block.pipeline.pipeline_node import OutputRoot

XRD_DATA_FILES = list((Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*"))


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    pipeline = xrd_block["pipeline"].clone()
    pipeline.set_caching_for_entire_pipeline(False)
    if f.suffix not in xrd_block["default_params"].accepted_file_extensions:
        return

    data = {"wavelength": 1.5, "metadata": {}, "computed": {}}

    pipeline_graph = [pipeline.parser_functions, *pipeline.processor_functions]

    graph_output = OutputRoot()
    entry_point_leaves = graph_output.add_pipeline(pipeline_graph)

    files = [f]
    checksums = ["Null"]
    for leaf in entry_point_leaves:
        leaf_files, leaf_checksums = [], []
        for index in range(len(files) - 1, -1, -1):
            file = files[index]
            if Path(file).suffix in leaf.file_input_type or "*" in leaf.file_input_type:
                leaf_files.append(Path(file))
                leaf_checksums.append(checksums[index])
                files.pop(index)
                checksums.pop(index)
        leaf.register_files_and_execute(leaf_files, leaf_checksums, "", data)

    result = graph_output.get_result()
    dfs = result["function_input"]
    df = dfs[0] if isinstance(dfs, list) else dfs
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
        assert "bokeh_plot_data" in result
