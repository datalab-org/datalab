import pathlib
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from pandas import Series

from pydatalab.pipeline_block.block_stages import (
    EventStage,
    ParserStage,
    PlotterStage,
    ProcessorStage,
)


# None testing
def none_function(function_input) -> "pd.DataFrame":  # type: ignore
    return None  # type: ignore


stages_with_none_function = [
    PlotterStage(none_function),  # type: ignore
    EventStage(none_function),  # type: ignore
]  # type: ignore


@pytest.mark.parametrize("stage", stages_with_none_function)
def test_each_block_response_with_none(stage):
    input_data = None
    response = stage.perform(input_data)  # type: ignore
    assert response is None


stages_with_none_tuple_function = [
    ParserStage(none_function, "*"),
    ProcessorStage(none_function, False),
]


@pytest.mark.parametrize("stage", stages_with_none_tuple_function)
def test_processor_response_with_none(stage):
    input_df = None
    response1, response2 = stage.perform(input_df)  # type: ignore
    assert response1 is None
    assert response2 is None


cache_stages_with_none = [
    ParserStage(none_function, "*"),
    ProcessorStage(none_function, False),  # type: ignore
]  # type: ignore


@pytest.mark.parametrize("stage", cache_stages_with_none)
def test_each_block_cache_response_with_none(stage):
    input_df = None
    cache_key, response, metadata = stage.perform_with_cache("Nothing", "Nothing", input_df)  # type: ignore
    assert response is None
    assert cache_key is None
    assert metadata is None


# Test processor with simple functions that return one dataframe
def doubler_function(function_input: "pd.DataFrame") -> "pd.DataFrame":
    return function_input.mul(2)


def test_processor_doubler():
    d = {"a": [1, 7, 8, 9, 2], "b": [2, 9, 3, 4, 5], "c": [3, 6, 5, 3, 6]}
    sample_df = pd.DataFrame(data=d)
    stage = ProcessorStage(doubler_function, False)
    result = stage.perform(sample_df)

    expected_d = {"a": [2, 14, 16, 18, 4], "b": [4, 18, 6, 8, 10], "c": [6, 12, 10, 6, 12]}
    expected_df = pd.DataFrame(data=expected_d)
    pd.testing.assert_frame_equal(expected_df, result[0])
    assert result[1] is None


def create_extra_column(function_input: "pd.DataFrame") -> "pd.DataFrame":
    function_input["New column"] = function_input["Column1"] + function_input["Column2"]
    return function_input


def test_processor_create_extra_column():
    d = {"Column1": [16, 73, 8, 94, 29], "Column2": [42, 39, 31, 14, 65], "c": [3, 6, 5, 3, 6]}
    sample_df = pd.DataFrame(data=d)
    stage = ProcessorStage(create_extra_column, False)
    result = stage.perform(sample_df)

    expected_d = {
        "Column1": [16, 73, 8, 94, 29],
        "Column2": [42, 39, 31, 14, 65],
        "c": [3, 6, 5, 3, 6],
        "New column": [58, 112, 39, 108, 94],
    }
    expected_df = pd.DataFrame(data=expected_d)
    pd.testing.assert_frame_equal(expected_df, result[0])
    assert result[1] is None


# testing inputting multiple dfs into processors and retrieving multiple dfs
def input_multiple_dfs(function_input: "list[pd.DataFrame]"):
    if len(function_input) < 2:
        return []
    return [doubler_function(function_input[0]), create_extra_column(function_input[1])]


def test_processor_input_multiple_dfs():
    d1 = {"Column1": [5, 23, 3, 94, 88], "Column2": [42, 39, 31, 7, 45], "c": [3, 4, 1, 4, 6]}
    d2 = {"Column1": [75, 78, 21, 66, 88], "Column2": [42, 39, 44, 89, 45], "c": [3, 4, 1, 4, 6]}
    sample_dfs = [pd.DataFrame(data=d1), pd.DataFrame(data=d2)]

    stage = ProcessorStage(input_multiple_dfs, True)
    result = stage.perform(sample_dfs)

    exp_d1 = {
        "Column1": [10, 46, 6, 188, 176],
        "Column2": [84, 78, 62, 14, 90],
        "c": [6, 8, 2, 8, 12],
    }
    exp_d2 = {
        "Column1": [75, 78, 21, 66, 88],
        "Column2": [42, 39, 44, 89, 45],
        "c": [3, 4, 1, 4, 6],
        "New column": [117, 117, 65, 155, 133],
    }
    exp_dfs = [pd.DataFrame(data=exp_d1), pd.DataFrame(data=exp_d2)]
    assert type(result[0]) is list
    pd.testing.assert_frame_equal(exp_dfs[0], result[0][0])
    pd.testing.assert_frame_equal(exp_dfs[1], result[0][1])
    assert result[1] is None


def sample_function_returns_metadata(function_input):
    return None, {
        "Hello": "This is a sample test output metadata",
        "Metadata": {"Some random value": 5, "Some new random value": 6},
        "Computed": {
            "Best thing ever": [1, 2, 3, 4, 5],
            "Another set of values": [6, 7, 8, 9, 10, 11, 12, 13],
        },
    }


stages_with_sample_function_returns_metadata = [
    ParserStage(sample_function_returns_metadata, "*"),  # type: ignore
    ProcessorStage(sample_function_returns_metadata, False),
]


@pytest.mark.parametrize("stage", stages_with_sample_function_returns_metadata)
def test_metadata_return_from_stage(stage):
    result, metadata = stage.perform(Path("None"))  # type : ignore
    assert result is None
    assert "Hello" in metadata
    assert "Metadata" in metadata
    assert "Computed" in metadata
    assert metadata["Hello"] == "This is a sample test output metadata"
    assert "Some random value" in metadata["Metadata"]
    assert "Some new random value" in metadata["Metadata"]
    assert metadata["Metadata"]["Some random value"] == 5
    assert metadata["Metadata"]["Some new random value"] == 6
    assert "Best thing ever" in metadata["Computed"]
    assert "Another set of values" in metadata["Computed"]
    assert metadata["Computed"]["Best thing ever"] == [1, 2, 3, 4, 5]
    assert metadata["Computed"]["Another set of values"] == [6, 7, 8, 9, 10, 11, 12, 13]


def doubler_function_with_metadata(function_input: "pd.DataFrame") -> "tuple[pd.DataFrame, dict]":
    return function_input.mul(2), {
        "Metadata": {"Operation": "Doubler"},
        "Computed": {
            "C Maximum Value": max(function_input["c"].mul(2)),
            "C Minimum Value": min(function_input["c"].mul(2)),
        },
    }


def test_processor_stage_using_perform_with_cache():
    stage = ProcessorStage(doubler_function_with_metadata, list_df_input=False)
    function_input = {"a": [9, 7, 1, 9, 2], "b": [2, 9, 11, 4, 5], "c": [3, 6, 5, 12, 6]}
    with patch("pandas.DataFrame.to_parquet") as mock_to_parquet:
        cache_key, result, metadata = stage.perform_with_cache(
            upstream_cache_key="upstream_key",
            folder=Path("tmp_path"),
            function_input=pd.DataFrame(data=function_input),
        )
        mock_to_parquet.assert_called_once()
        assert (Path("tmp_path") / f"{cache_key}.parquet") == mock_to_parquet.call_args[0][0]
        function_output = {
            "a": [18, 14, 2, 18, 4],
            "b": [4, 18, 22, 8, 10],
            "c": [6, 12, 10, 24, 12],
        }
        pd.testing.assert_frame_equal(pd.DataFrame(function_output), result)
        assert "Metadata" in metadata
        assert "Computed" in metadata
        assert "Operation" in metadata["Metadata"]
        assert metadata["Metadata"]["Operation"] == "Doubler"
        assert "C Maximum Value" in metadata["Computed"]
        assert "C Minimum Value" in metadata["Computed"]
        assert metadata["Computed"]["C Maximum Value"] == 24
        assert metadata["Computed"]["C Minimum Value"] == 6


def empty_test_function(df: pd.DataFrame, arg1: int, arg2: int) -> pd.DataFrame:
    return pd.DataFrame()


# tests the arg checker
def test_input_args():
    stage = ProcessorStage(empty_test_function, False)
    arg_check = stage.check_args(["arg1", "arg2"])
    assert arg_check is True
    arg_check_2 = stage.check_args(["arg3", "arg5"])
    assert arg_check_2 is False
    arg_check_3 = stage.check_args(["arg4", "arg6", "arg1", "arg2"])
    assert arg_check_3 is True


def empty_parser_function(path_name: str | pathlib.Path):
    df = pd.DataFrame()
    df = pd.DataFrame(
        [[path_name]],
        index=Series([0]),
        columns=Series(
            [
                "special path name",
            ]
        ),
    )
    data = {}
    data["metadata"] = {}
    data["metadata"]["useless_values"] = 1
    data["computed"] = {}
    data["computed"]["useless_important_values"] = 45
    return df, data


def test_parser_perform():
    stage = ParserStage(empty_parser_function, ["*"])
    df, metadata = stage.perform(Path("example_file"))
    assert "special path name" in df
    assert df.loc[0]["special path name"] == Path("example_file")
    assert "metadata" in metadata
    assert "useless_values" in metadata["metadata"]
    assert metadata["metadata"]["useless_values"] == 1
    assert "computed" in metadata
    assert "useless_important_values" in metadata["computed"]
    assert metadata["computed"]["useless_important_values"] == 45
    assert metadata["metadata"]["original_filenames"] == ["example_file"]


def test_validate_input_for_parser():
    stage = ParserStage(empty_parser_function, [".csv", ".exe"])
    assert stage.validate_input(Path("hello.csv")) == True
    assert stage.validate_input(Path("instagram.exe")) == True
    assert stage.validate_input(Path("example_file")) == False
    assert stage.validate_input(Path("Also_should_fail.cs")) == False
