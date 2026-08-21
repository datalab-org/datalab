import pandas as pd

from pydatalab.pipeline_block.block_stages import ParserStage, PlotterStage, ProcessorStage
from pydatalab.pipeline_block.pipeline.pipeline_node import OutputRoot


def example_test_parser_csv(filename) -> pd.DataFrame:
    return pd.DataFrame({"A": [1, 2, 3, 4, 5]})


def example_test_catch_all_parser(filename) -> pd.DataFrame:
    return pd.DataFrame({"B": [6, 7, 8, 9, 10]})


def example_test_processor_csv(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(df.mul(2))


def example_test_catch_all_processor(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(df.mul(4))


def test_graph_creation_pipeline_node():
    # constructs a pipeline from scratch instead of using the Pipeline class (Not recommended for regular use)
    pipeline = [
        [
            ParserStage(function=example_test_parser_csv, file_extension=".csv"),
            ParserStage(function=example_test_catch_all_parser, file_extension="*"),
        ],
        [
            ProcessorStage(function=example_test_processor_csv, file_extension=".csv"),
            ProcessorStage(function=example_test_catch_all_processor, file_extension="*"),
        ],
        [PlotterStage(function=lambda x: x, list_df_input=True)],
    ]
    graph_root: OutputRoot = OutputRoot()

    endpoints = graph_root.add_pipeline(pipeline)

    assert len(endpoints) == 2
    # assertions for branch one
    assert endpoints[0].file_input_type == {
        ".csv",
    }

    endpoint_0_parent = endpoints[0].parent_node
    assert endpoint_0_parent.stage.stage.value == "parser"
    assert endpoint_0_parent.stage.function.__name__ == "example_test_parser_csv"

    endpoint_0_grandparent = endpoint_0_parent.parent_node
    assert endpoint_0_grandparent.stage.stage.value == "processor"
    assert endpoint_0_grandparent.stage.function.__name__ == "example_test_processor_csv"

    endpoint_0_great_grandparent = endpoint_0_grandparent.parent_node
    assert endpoint_0_great_grandparent.stage.stage.value == "plotter"
    assert endpoint_0_great_grandparent.stage.function.__name__ == "<lambda>"

    # assertions for branch two
    assert endpoints[1].file_input_type == {
        "*",
    }

    endpoint_1_parent = endpoints[1].parent_node
    assert endpoint_1_parent.stage.stage.value == "parser"
    assert endpoint_1_parent.stage.function.__name__ == "example_test_catch_all_parser"

    endpoint_1_grandparent = endpoint_1_parent.parent_node
    assert endpoint_1_grandparent.stage.stage.value == "processor"
    assert endpoint_1_grandparent.stage.function.__name__ == "example_test_catch_all_processor"

    endpoint_1_great_grandparent = endpoint_1_grandparent.parent_node
    assert endpoint_1_great_grandparent.stage.stage.value == "plotter"
    assert endpoint_1_great_grandparent.stage.function.__name__ == "<lambda>"

    assert endpoint_0_great_grandparent == endpoint_1_great_grandparent


def example_test_processor_csv_2(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(df.mul(10))


def example_test_catch_all_processor_2(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(df.mul(20))


def test_graph_creation_with_two_layer_processor():
    # constructs a pipeline from scratch instead of using the Pipeline class (Not recommended for regular use)
    pipeline = [
        [
            ParserStage(function=example_test_parser_csv, file_extension=".csv"),
            ParserStage(function=example_test_catch_all_parser, file_extension="*"),
        ],
        [
            ProcessorStage(function=example_test_processor_csv, file_extension=".csv"),
            ProcessorStage(function=example_test_catch_all_processor, file_extension="*"),
        ],
        [
            ProcessorStage(function=example_test_processor_csv_2, file_extension=".csv"),
            ProcessorStage(function=example_test_catch_all_processor_2, file_extension="*"),
        ],
        [PlotterStage(function=lambda x: x, list_df_input=True)],
    ]
    graph_root: OutputRoot = OutputRoot()

    endpoints = graph_root.add_pipeline(pipeline)

    assert len(endpoints) == 2
    # assertions for branch one
    assert endpoints[0].file_input_type == {
        ".csv",
    }

    endpoint_0_parent = endpoints[0].parent_node
    assert endpoint_0_parent.stage.stage.value == "parser"
    assert endpoint_0_parent.stage.function.__name__ == "example_test_parser_csv"

    endpoint_0_grandparent = endpoint_0_parent.parent_node
    assert endpoint_0_grandparent.stage.stage.value == "processor"
    assert endpoint_0_grandparent.stage.function.__name__ == "example_test_processor_csv"

    endpoint_0_great_grandparent = endpoint_0_grandparent.parent_node
    assert endpoint_0_great_grandparent.stage.stage.value == "processor"
    assert endpoint_0_great_grandparent.stage.function.__name__ == "example_test_processor_csv_2"

    endpoint_0_great_great_grandparent = endpoint_0_great_grandparent.parent_node
    assert endpoint_0_great_great_grandparent.stage.stage.value == "plotter"
    assert endpoint_0_great_great_grandparent.stage.function.__name__ == "<lambda>"

    # assertions for branch two
    assert endpoints[1].file_input_type == {
        "*",
    }

    endpoint_1_parent = endpoints[1].parent_node
    assert endpoint_1_parent.stage.stage.value == "parser"
    assert endpoint_1_parent.stage.function.__name__ == "example_test_catch_all_parser"

    endpoint_1_grandparent = endpoint_1_parent.parent_node
    assert endpoint_1_grandparent.stage.stage.value == "processor"
    assert endpoint_1_grandparent.stage.function.__name__ == "example_test_catch_all_processor"

    endpoint_1_great_grandparent = endpoint_1_grandparent.parent_node
    assert endpoint_1_great_grandparent.stage.stage.value == "processor"
    assert (
        endpoint_1_great_grandparent.stage.function.__name__ == "example_test_catch_all_processor_2"
    )

    endpoint_1_great_great_grandparent = endpoint_1_great_grandparent.parent_node
    assert endpoint_1_great_great_grandparent.stage.stage.value == "plotter"
    assert endpoint_1_great_great_grandparent.stage.function.__name__ == "<lambda>"

    assert endpoint_0_great_great_grandparent == endpoint_1_great_great_grandparent
