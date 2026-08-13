"""
This file tests the base pipeline block functionality
which is split between the Pipeline class, the PipelineBlockManager and the DataBlockDefaults schema.
"""

from pathlib import Path
from unittest import mock

import pandas as pd

from pydatalab.config import CONFIG
from pydatalab.pipeline_block.base import DataBlockDefaults
from pydatalab.pipeline_block.block_manager import PipelineBlockManager, _perform_operations
from pydatalab.pipeline_block.block_stages import ParserStage, ProcessorStage
from pydatalab.pipeline_block.pipeline import Pipeline, _add_output_onto_list, _merge_dictionaries
from pydatalab.pipeline_block.utils import generate_js_callback_single_float_parameter


def test_base_block():
    block_manager = PipelineBlockManager()
    block_manager.register_block(Pipeline(), DataBlockDefaults())
    block = block_manager.create_block_data("DataBlock", item_id="test-id")
    test_event = {"event_name": "null_event", "kwargs": {"a": 1, "b": 2, "c": 1.2, "d": "string"}}
    block_manager.process_events(block, test_event)
    assert block["kwargs"]["a"] == 1
    assert block["kwargs"]["b"] == 2
    assert block["kwargs"]["c"] == 1.2
    assert block["kwargs"]["d"] == "string"


def test_callback():
    callback = generate_js_callback_single_float_parameter(
        "set_wavelength", "wavelength", block_id="test", throttled=False
    )
    assert (
        callback
        == """const block_event = new CustomEvent('block-event', {
    detail: {
        block_id: 'test',
        event_name: 'set_wavelength',
        wavelength: (cb_obj.value ?? cb_obj.text),
    }, bubbles: true
});
document.dispatchEvent(block_event);"""
    )


@mock.patch("pydatalab.pipeline_block.block_manager.get_file_info_by_id")
def test_file_acceptance_logic(get_file_info_by_id):
    get_file_info_by_id.return_value = {
        "location": "TEST_FILE_INFO.txt",
        "checksums": "TEST_CHECKSUM",
    }
    pipeline_mock = Pipeline()
    pipeline_mock.perform_entire_pipeline = mock.MagicMock(return_value=None)
    block_data = {"file_id": "12345678"}

    _perform_operations(
        DataBlockDefaults(multi_file=False, accepted_file_extensions=(".txt", ".csv")),
        pipeline_mock,
        block_data,
    )

    assert pipeline_mock.perform_entire_pipeline.is_called
    assert pipeline_mock.perform_entire_pipeline.call_count == 1
    pipeline_mock.perform_entire_pipeline.assert_called_once_with(
        data=block_data,
        file_folder=Path(CONFIG.FILE_DIRECTORY),
        files=[Path("TEST_FILE_INFO.txt")],
        checksums=["TEST_CHECKSUM"],
    )


@mock.patch("pydatalab.pipeline_block.block_manager.get_file_info_by_id")
@mock.patch("pydatalab.pipeline_block.block_manager.LOGGER")
def test_should_fail_file_type(logger, get_file_info_by_id):
    get_file_info_by_id.return_value = {
        "location": "TEST_FILE_INFO.exe",
        "checksums": "TEST_CHECKSUM",
    }
    pipeline_mock = Pipeline()
    pipeline_mock.perform_entire_pipeline = mock.MagicMock(return_value=None)
    block_data = {"file_id": "12345678"}
    result = _perform_operations(
        DataBlockDefaults(multi_file=False, accepted_file_extensions=(".txt", ".csv")),
        pipeline_mock,
        block_data,
    )
    assert pipeline_mock.perform_entire_pipeline.call_count == 0
    assert result is None
    assert logger.warning.call_count == 1
    logger.warning.assert_called_once_with(
        "File with extension `%s` is not an acceptable file extension, (acceptable parsers: `%s`)",
        ".exe",
        (".txt", ".csv"),
    )


def test_merge_dictionaries():
    dict_original = {
        "a": 1,
        "b": 2,
        "computed": {"value1": 3, "value2": 4},
        "metadata": {"file_type": ".csv"},
    }
    dict_update = {
        "e": "hello",
        "computed": {"value3": 5, "value4": 6},
        "metadata": {"file_type": ".json"},
    }
    result = _merge_dictionaries(dict_original, dict_update)
    assert "a" in result
    assert "computed" in result
    assert "metadata" in result
    assert "e" in result
    assert "b" in result
    assert result["a"] == 1
    assert result["b"] == 2
    assert "value1" in result["computed"]
    assert "value2" in result["computed"]
    assert "value3" in result["computed"]
    assert "value4" in result["computed"]
    assert result["computed"]["value1"] == 3
    assert result["computed"]["value2"] == 4
    assert result["computed"]["value3"] == 5
    assert result["computed"]["value4"] == 6
    assert "file_type" in result["metadata"]
    assert result["metadata"]["file_type"] == ".json"


def test_merge_dictionaries_with_lists_in():
    dict_original = {"list1": [1, 2, 3, 4]}
    dict_update = {"list1": [5, 6, 7, 8, 9]}
    result = _merge_dictionaries(dict_original, dict_update)
    assert "list1" in result
    assert result["list1"] == [1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_add_output_onto_list_should_return_false_when_inputting_none():
    original_checksums = []
    output_dfs = []
    result = _add_output_onto_list(None, original_checksums, output_dfs, None)
    assert result == False
    assert original_checksums == []
    assert output_dfs == []


def test_add_output_onto_list_should_return_true_when_inputting_list():
    original_checksums = []
    output_dfs = []
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    result = _add_output_onto_list("abc", original_checksums, output_dfs, df)
    assert result is True
    assert original_checksums == ["abc"]
    assert output_dfs == [df]


@mock.patch("pydatalab.pipeline_block.pipeline.BlockStage.perform_with_optional_cache")
@mock.patch("pydatalab.pipeline_block.pipeline.PlotterStage.perform")
def test_perform_entire_pipeline_without_metadata(
    perform,
    perform_with_optional_cache,
):
    pipeline = Pipeline(parser=ParserStage(lambda x: x, file_extension="*"))  # type: ignore
    data = {}
    perform.return_value = "Example bokeh return thing"
    df = pd.DataFrame({"a": [6, 7, 8], "b": [9, 10, 11]})
    perform_with_optional_cache.return_value = ("Checksum2", df, {})
    data_result = pipeline.perform_entire_pipeline(
        data=data,
        file_folder="random folder",
        files=[Path("File One.csv")],
        checksums=["TEST_CHECKSUM"],
    )
    assert "bokeh_plot_data" in data_result
    assert data_result["bokeh_plot_data"] == "Example bokeh return thing"

    assert perform_with_optional_cache.call_count == 2
    assert perform_with_optional_cache.call_args_list[0][0] == (
        "TEST_CHECKSUM",
        "random folder",
        Path("File One.csv"),
    )
    assert perform_with_optional_cache.call_args_list[1][0] == ("Checksum2", "random folder", df)

    assert perform.call_count == 1
    pd.testing.assert_frame_equal(perform.call_args_list[0][0][0], df)


@mock.patch("pydatalab.pipeline_block.pipeline.BlockStage.perform_with_optional_cache")
@mock.patch("pydatalab.pipeline_block.pipeline.PlotterStage.perform")
def test_perform_entire_pipeline_with_metadata(
    perform,
    perform_with_optional_cache,
):
    pipeline = Pipeline(parser=ParserStage(lambda x: x, file_extension="*"))  # type: ignore
    data = {}
    perform.return_value = "Example bokeh return thing"
    df = pd.DataFrame({"a": [6, 7, 8], "b": [9, 10, 11]})
    perform_with_optional_cache.return_value = (
        "Checksum2",
        df,
        {
            "metadata": {"name": "random test"},
            "computed": {"value": 45, "old_value": 75},
            "wavelength": 7.5,
        },
    )
    data_result = pipeline.perform_entire_pipeline(
        data=data,
        file_folder="random folder",
        files=[Path("File One.csv")],
        checksums=["TEST_CHECKSUM"],
    )
    assert "bokeh_plot_data" in data_result
    assert "metadata" in data_result
    assert "computed" in data_result
    assert "wavelength" in data_result
    assert "name" in data_result["metadata"]
    assert data_result["metadata"]["name"] == "random test"
    assert "value" in data_result["computed"]
    assert data_result["computed"]["value"] == 45
    assert "old_value" in data_result["computed"]
    assert data_result["computed"]["old_value"] == 75
    assert data_result["bokeh_plot_data"] == "Example bokeh return thing"

    assert perform_with_optional_cache.call_count == 2
    assert perform_with_optional_cache.call_args_list[0][0] == (
        "TEST_CHECKSUM",
        "random folder",
        Path("File One.csv"),
    )
    assert perform_with_optional_cache.call_args_list[1][0] == ("Checksum2", "random folder", df)

    assert perform.call_count == 1
    pd.testing.assert_frame_equal(perform.call_args_list[0][0][0], df)


def sample_parser(filename: Path | str):
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}), {
        "filename inputted from parser": filename,
        "big_number": 8,
    }


def sample_double_processor(df: pd.DataFrame, big_number) -> tuple[pd.DataFrame, dict]:
    return df.mul(2), {
        "another big number": big_number * 2,
        "metadata": {"parser": "data"},
        "computed": {"data": df.mul(2)},
    }


def test_perform_entire_pipeline_without_mocks_with_metadata():
    pipeline = Pipeline(
        parser=ParserStage(sample_parser, file_extension="*", caching=False),
        processor=ProcessorStage(sample_double_processor, list_df_input=False, caching=False),
    )
    data = {}
    data_result = pipeline.perform_entire_pipeline(
        data=data,
        file_folder="random folder",
        files=[Path("File One.csv")],
        checksums=["TEST_CHECKSUM"],
    )

    assert "bokeh_plot_data" in data_result
    assert "filename inputted from parser" in data_result
    assert data_result["filename inputted from parser"] == Path("File One.csv")
    assert "big_number" in data_result
    assert data_result["big_number"] == 8
    assert "another big number" in data_result
    assert data_result["another big number"] == 16
    assert "metadata" in data_result
    assert "parser" in data_result["metadata"]
    assert data_result["metadata"]["parser"] == "data"
    assert "computed" in data_result
    assert "data" in data_result["computed"]
    pd.testing.assert_frame_equal(
        data_result["computed"]["data"], pd.DataFrame({"a": [2, 4, 6], "b": [8, 10, 12]})
    )
