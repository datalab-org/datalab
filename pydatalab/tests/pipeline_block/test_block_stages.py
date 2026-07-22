import pandas as pd
import pytest

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
    ParserStage(none_function, "*"),
    ProcessorStage(none_function, False),  # type: ignore
    PlotterStage(none_function),  # type: ignore
    EventStage(none_function),
]  # type: ignore


@pytest.mark.parametrize("stage", stages_with_none_function)
def test_each_block_response_with_none(stage):
    input_df = None
    response = stage.perform(input_df)  # type: ignore
    assert response is None


cache_stages_with_none = [
    ParserStage(none_function, "*"),
    ProcessorStage(none_function, False),  # type: ignore
]  # type: ignore


@pytest.mark.parametrize("stage", cache_stages_with_none)
def test_each_block_cache_response_with_none(stage):
    input_df = None
    cache_key, response = stage.perform_with_cache("Nothing", "Nothing", input_df)  # type: ignore
    assert response is None
    assert cache_key is None


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
    pd.testing.assert_frame_equal(expected_df, result)


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
    pd.testing.assert_frame_equal(expected_df, result)


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
    assert type(result) is list
    pd.testing.assert_frame_equal(exp_dfs[0], result[0])
    pd.testing.assert_frame_equal(exp_dfs[1], result[1])


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
