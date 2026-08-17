"""
This file tests the base pipeline block functionality
which is split between the pipeline class, the PipelineBlockManager and the DataBlockDefaults schema.
"""

from pathlib import Path
from unittest import mock

import pandas as pd

from pydatalab.config import CONFIG
from pydatalab.pipeline_block.base import DataBlockDefaults
from pydatalab.pipeline_block.block_manager import PipelineBlockManager, _perform_operations
from pydatalab.pipeline_block.block_stages import ParserStage, PlotterStage, ProcessorStage
from pydatalab.pipeline_block.pipeline import Pipeline
from pydatalab.pipeline_block.pipeline.pipeline import _add_output_onto_list
from pydatalab.pipeline_block.utils import (
    generate_js_callback_single_float_parameter,
    merge_dictionaries,
)


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
    result = merge_dictionaries(dict_original, dict_update)
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
    result = merge_dictionaries(dict_original, dict_update)
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


def test_perform_entire_pipeline_without_metadata():
    sample_mock_parser: BlockStage = ParserStage(lambda x: x, file_extension="*")  # type: ignore
    sample_mock_processor = ProcessorStage(lambda x: x, file_extension="*", list_df_input=False)  # type: ignore
    sample_mock_plotter = PlotterStage(lambda x: x)  # type : ignore
    with (
        mock.patch.object(
            sample_mock_processor, "perform_with_optional_cache"
        ) as mock_perform_processor,
        mock.patch.object(sample_mock_parser, "perform_with_optional_cache") as mock_perform_parser,
        mock.patch.object(
            sample_mock_plotter, "perform_with_optional_cache"
        ) as mock_perform_plotter,
    ):
        pipeline = Pipeline(
            parser=sample_mock_parser, processor=sample_mock_processor, plotter=sample_mock_plotter
        )  # type: ignore

        mock_perform_parser.return_value = {
            "upstream_cache_key": "Checksum1",
            "folder": "random folder",
            "function_input": "Parser response",
            "data": {},
        }

        df = pd.DataFrame({"a": [6, 7, 8], "b": [9, 10, 11]})
        mock_perform_processor.return_value = {
            "upstream_cache_key": "Checksum2 from processor",
            "folder": "none",
            "function_input": df,
            "data": {},
        }
        mock_perform_plotter.return_value = {
            "upstream_cache_key": "Checksum3",
            "folder": "NaN",
            "function_input": "Example bokeh return thing",
            "data": {},
        }

        data = {}
        data_result = pipeline.perform_entire_pipeline(
            data=data,
            file_folder="random folder",
            files=[Path("File One.csv")],
            checksums=["TEST_CHECKSUM"],
        )
        assert "bokeh_plot_data" in data_result
        assert data_result["bokeh_plot_data"] == "Example bokeh return thing"
        assert "metadata" in data_result
        assert data_result["metadata"] == {}
        assert "computed" in data_result
        assert data_result["computed"] == {}

        assert mock_perform_parser.call_count == 1
        assert mock_perform_processor.call_count == 1
        assert mock_perform_plotter.call_count == 1

        assert "upstream_cache_key" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["upstream_cache_key"] == "TEST_CHECKSUM"
        assert "folder" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["function_input"] == Path("File One.csv")
        assert "data" in mock_perform_parser.call_args_list[0][1]

        assert "upstream_cache_key" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["upstream_cache_key"] == "Checksum1"
        assert "folder" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["function_input"] == "Parser response"
        assert "data" in mock_perform_processor.call_args_list[0][1]

        assert "upstream_cache_key" in mock_perform_plotter.call_args_list[0][1]
        assert (
            mock_perform_plotter.call_args_list[0][1]["upstream_cache_key"]
            == "Checksum2 from processor"
        )
        assert "folder" in mock_perform_plotter.call_args_list[0][1]
        assert mock_perform_plotter.call_args_list[0][1]["folder"] == "none"
        assert "function_input" in mock_perform_plotter.call_args_list[0][1]
        pd.testing.assert_frame_equal(
            mock_perform_plotter.call_args_list[0][1]["function_input"], df
        )


def test_perform_entire_pipeline_with_metadata():
    sample_mock_parser: BlockStage = ParserStage(lambda x: x, file_extension="*")  # type: ignore
    sample_mock_processor = ProcessorStage(lambda x: x, file_extension="*", list_df_input=False)  # type: ignore
    sample_mock_plotter = PlotterStage(lambda x: x)  # type : ignore
    with (
        mock.patch.object(
            sample_mock_processor, "perform_with_optional_cache"
        ) as mock_perform_processor,
        mock.patch.object(sample_mock_parser, "perform_with_optional_cache") as mock_perform_parser,
        mock.patch.object(
            sample_mock_plotter, "perform_with_optional_cache"
        ) as mock_perform_plotter,
    ):
        pipeline = Pipeline(
            parser=sample_mock_parser, processor=sample_mock_processor, plotter=sample_mock_plotter
        )  # type: ignore
        data = {}
        mock_perform_parser.return_value = {
            "upstream_cache_key": "Checksum1",
            "function_input": "Parser response",
            "folder": "random folder",
            "data": {},
        }
        df = pd.DataFrame({"a": [6, 7, 8], "b": [9, 10, 11]})
        mock_perform_processor.return_value = {
            "upstream_cache_key": "Checksum2",
            "function_input": df,
            "folder": "random folder",
            "data": {
                "metadata": {"name": "random test"},
                "computed": {"value": 45, "old_value": 75},
                "wavelength": 7.5,
            },
        }
        mock_perform_plotter.return_value = {
            "upstream_cache_key": "Checksum3",
            "folder": "random folder",
            "function_input": "Example bokeh return thing",
            "data": {},
        }
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
        assert mock_perform_processor.call_count == 1
        assert mock_perform_plotter.call_count == 1
        assert mock_perform_parser.call_count == 1

        assert "upstream_cache_key" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["upstream_cache_key"] == "TEST_CHECKSUM"
        assert "folder" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["function_input"] == Path("File One.csv")
        assert "data" in mock_perform_parser.call_args_list[0][1]

        assert "upstream_cache_key" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["upstream_cache_key"] == "Checksum1"
        assert "folder" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["function_input"] == "Parser response"
        assert "data" in mock_perform_processor.call_args_list[0][1]

        assert "upstream_cache_key" in mock_perform_plotter.call_args_list[0][1]
        assert mock_perform_plotter.call_args_list[0][1]["upstream_cache_key"] == "Checksum2"
        assert "folder" in mock_perform_plotter.call_args_list[0][1]
        assert mock_perform_plotter.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_plotter.call_args_list[0][1]
        pd.testing.assert_frame_equal(
            mock_perform_plotter.call_args_list[0][1]["function_input"], df
        )


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


def txt_csv_parser_mocked(filename: Path | str) -> pd.DataFrame:
    return pd.DataFrame({"a": [3, 5, 1], "b": [8, 1, 15]})


def exe_bin_parser_mocked(filename: Path | str) -> pd.DataFrame:
    return pd.DataFrame({"c": [12, 1, 8], "b": [7, 4, 2]})


def sample_quad_processor(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    return df.mul(4), {"computed": {"quad_data": df.mul(4)}}


def sample_treble_processor(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    return df.mul(3), {"computed": {"treble_data": df.mul(3)}}


def combiner_processor(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(dfs)


def test_perform_entire_pipeline_with_specific_processor_file_file_types():
    pipeline = Pipeline(
        parser=[
            ParserStage(txt_csv_parser_mocked, file_extension=[".csv", ".txt"], caching=False),
            ParserStage(exe_bin_parser_mocked, file_extension=[".exe", ".bin"], caching=False),
        ],
        processor=[
            [
                ProcessorStage(
                    sample_quad_processor,
                    list_df_input=False,
                    caching=False,
                    file_extension=[".csv", ".txt"],
                ),
                ProcessorStage(
                    sample_treble_processor,
                    list_df_input=False,
                    caching=False,
                    file_extension=[".exe", ".bin"],
                ),
            ],
            [ProcessorStage(combiner_processor, list_df_input=True, caching=False)],
        ],
    )
    data = {}
    data_result = pipeline.perform_entire_pipeline(
        data=data,
        file_folder="random folder",
        files=[
            Path("Route_through_one.csv"),
            Path("Route_through_two.bin"),
            Path("Route_through_one.txt"),
            Path("Route_through_two.exe"),
        ],
        checksums=["TEST.csvchecksum", "TEST.binchecksum", "TEST.txtchecksum", "TEST.exechecksum"],
    )
    assert "bokeh_plot_data" in data_result
    assert "computed" in data_result
    assert "quad_data" in data_result["computed"]
    assert "treble_data" in data_result["computed"]
    pd.testing.assert_frame_equal(
        data_result["computed"]["quad_data"], pd.DataFrame({"a": [12, 20, 4], "b": [32, 4, 60]})
    )
    pd.testing.assert_frame_equal(
        data_result["computed"]["treble_data"], pd.DataFrame({"c": [36, 3, 24], "b": [21, 12, 6]})
    )


def test_perform_entire_pipeline_with_less_than_parser_file_types():
    pipeline = Pipeline(
        parser=[
            ParserStage(
                lambda x: pd.DataFrame({"a": [3, 5, 1], "b": [8, 1, 15]}),
                file_extension=[".csv", ".txt"],
                caching=False,
            ),
            ParserStage(
                lambda x: pd.DataFrame({"c": [12, 1, 8], "b": [7, 4, 2]}),
                file_extension=[".exe", ".bin"],
                caching=False,
            ),
            ParserStage(
                lambda x: pd.DataFrame({"c": [3, 0.5, 12], "b": [6, 10, 3]}),
                file_extension=[".insta", ".win"],
                caching=False,
            ),
        ],
        processor=[
            [
                ProcessorStage(
                    lambda df: (df.mul(3), {"computed": {"treble_data": df.mul(3)}}),
                    list_df_input=False,
                    caching=False,
                    file_extension=[".csv", ".txt"],
                ),
                ProcessorStage(
                    lambda df: (df.mul(6), {"computed": {"septuple_data": df.mul(7)}}),
                    list_df_input=False,
                    caching=False,
                    file_extension=[".exe", ".bin"],
                ),
                ProcessorStage(
                    lambda df: (df.mul(17), {"computed": {"septendecuple_data": df.mul(17)}}),
                    list_df_input=False,
                    caching=False,
                    file_extension=[".insta", ".win"],
                ),
            ],
            [ProcessorStage(combiner_processor, list_df_input=True, caching=False)],
        ],
    )
    data = {}
    data_result = pipeline.perform_entire_pipeline(
        data=data,
        file_folder="random folder",
        files=[Path("Route_through_one.csv"), Path("Route_through_two.bin")],
        checksums=["TEST.csvchecksum", "TEST.binchecksum"],
    )
    assert "bokeh_plot_data" in data_result
    assert data_result["bokeh_plot_data"] != []
    assert "computed" in data_result
    assert "septuple_data" in data_result["computed"]
    assert "treble_data" in data_result["computed"]
    pd.testing.assert_frame_equal(
        data_result["computed"]["treble_data"], pd.DataFrame({"a": [9, 15, 3], "b": [24, 3, 45]})
    )
    pd.testing.assert_frame_equal(
        data_result["computed"]["septuple_data"],
        pd.DataFrame({"c": [84, 7, 56], "b": [49, 28, 14]}),
    )
    assert "septendecuple_data" not in data_result["computed"]


def test_does_not_fail_silently_when_receiving_no_further_inputs():
    """
    Check whether when having two parser and only one file which only cause the first to fire
    That the other notifies the other that there are no inputs and correctly cascades through
    So that the plotter gets called.
    """
    sample_mock_parser: BlockStage = ParserStage(lambda x: x, file_extension=".txt")  # type: ignore
    sample_mock_parser_csv: BlockStage = ParserStage(lambda x: x, file_extension=".csv")  # type: ignore
    sample_mock_processor = ProcessorStage(lambda x: x, file_extension="*", list_df_input=False)  # type: ignore
    sample_mock_plotter = PlotterStage(lambda x: x)  # type : ignore
    with (
        mock.patch.object(
            sample_mock_processor, "perform_with_optional_cache"
        ) as mock_perform_processor,
        mock.patch.object(sample_mock_parser, "perform_with_optional_cache") as mock_perform_parser,
        mock.patch.object(
            sample_mock_parser_csv, "perform_with_optional_cache"
        ) as mock_perform_csv,
        mock.patch.object(
            sample_mock_plotter, "perform_with_optional_cache"
        ) as mock_perform_plotter,
    ):
        pipeline = Pipeline(
            parser=[sample_mock_parser, sample_mock_parser_csv],
            processor=sample_mock_processor,
            plotter=sample_mock_plotter,
        )  # type: ignore

        mock_perform_parser.return_value = {
            "upstream_cache_key": "Checksum1",
            "folder": "random folder",
            "function_input": "Parser response",
            "data": {},
        }
        mock_perform_csv.return_value = {
            "upstream_cache_key": "Checksum4",
            "folder": "random folder 4",
            "function_input": "Parser 2 response",
            "data": {},
        }

        df = pd.DataFrame({"a": [6, 7, 8], "b": [9, 10, 11]})
        mock_perform_processor.return_value = {
            "upstream_cache_key": "Checksum2 from processor",
            "folder": "none",
            "function_input": df,
            "data": {},
        }
        mock_perform_plotter.return_value = {
            "upstream_cache_key": "Checksum3",
            "folder": "NaN",
            "function_input": "Example bokeh return thing",
            "data": {},
        }

        data = {}
        data_result = pipeline.perform_entire_pipeline(
            data=data,
            file_folder="random folder",
            files=[Path("File One.txt")],
            checksums=["TEST_CHECKSUM"],
        )
        assert "bokeh_plot_data" in data_result
        assert "bokeh_plot_data" != []
        assert data_result["bokeh_plot_data"] == "Example bokeh return thing"
        assert "metadata" in data_result
        assert data_result["metadata"] == {}
        assert "computed" in data_result
        assert data_result["computed"] == {}

        assert mock_perform_parser.call_count == 1
        assert mock_perform_csv.call_count == 0
        assert mock_perform_processor.call_count == 1
        assert mock_perform_plotter.call_count == 1

        assert "upstream_cache_key" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["upstream_cache_key"] == "TEST_CHECKSUM"
        assert "folder" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_parser.call_args_list[0][1]
        assert mock_perform_parser.call_args_list[0][1]["function_input"] == Path("File One.txt")
        assert "data" in mock_perform_parser.call_args_list[0][1]

        assert "upstream_cache_key" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["upstream_cache_key"] == "Checksum1"
        assert "folder" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["folder"] == "random folder"
        assert "function_input" in mock_perform_processor.call_args_list[0][1]
        assert mock_perform_processor.call_args_list[0][1]["function_input"] == "Parser response"
        assert "data" in mock_perform_processor.call_args_list[0][1]

        assert "upstream_cache_key" in mock_perform_plotter.call_args_list[0][1]
        assert (
            mock_perform_plotter.call_args_list[0][1]["upstream_cache_key"]
            == "Checksum2 from processor"
        )
        assert "folder" in mock_perform_plotter.call_args_list[0][1]
        assert mock_perform_plotter.call_args_list[0][1]["folder"] == "none"
        assert "function_input" in mock_perform_plotter.call_args_list[0][1]
        pd.testing.assert_frame_equal(
            mock_perform_plotter.call_args_list[0][1]["function_input"], df
        )
