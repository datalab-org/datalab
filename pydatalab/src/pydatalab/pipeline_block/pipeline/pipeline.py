import copy
from pathlib import Path
from typing import Any

import bokeh.embed
import pandas as pd
from pandas import DataFrame

from pydatalab.logger import LOGGER
from pydatalab.pipeline_block.block_stages import (
    EventStage,
    ParserStage,
    PlotterStage,
    ProcessorStage,
)

__all__ = ["Pipeline"]

from pydatalab.pipeline_block.block_stages.abstract_stage import BlockStage
from pydatalab.pipeline_block.pipeline.pipeline_node import FileInputLeaf, OutputRoot
from pydatalab.pipeline_block.utils import merge_dictionaries


def _add_output_onto_list(
    new_checksum, original_checksums: list[str], output_dfs: list[DataFrame], result_df
):
    """
    Adds the output from a BlockStage onto a list.
    :param new_checksum: The new checksum from the parser
    :param original_checksums: The original list of checksums
    :param output_dfs: The list of dataframes to append to.
    :param result_df: The resulting dataframes to add from the BlockStage.
    :return: Whether the resulting dataframe was added successfully or not.
    """
    if result_df is not None:
        if type(result_df) is not list:
            result_df = [result_df]
        if type(new_checksum) is not list:
            new_checksum = [new_checksum]
        output_dfs.extend(result_df)
        original_checksums.extend(new_checksum)
        return True
    return False


class Pipeline:
    parser_functions: list[ParserStage]
    """A list of methods that will parse files for this datablock."""

    processor_functions: list[list[ProcessorStage]]
    """A list of processor stages that will operate on the data for this datablock."""

    plotter_function: PlotterStage
    """ The plotter that will create the plot from the data in this datablock."""

    event_functions: dict[str, EventStage]
    """ The event stage functions, used when calling an event for a partial parameter update """

    @staticmethod
    def plotter(df: pd.DataFrame) -> Any:
        from pydatalab.bokeh_plots import selectable_axes_plot

        if df is None:
            return None
        plot = selectable_axes_plot(
            df,
            plot_points=True,
            plot_line=False,
            show_table=True,
        )
        return bokeh.embed.json_item(plot)

    @staticmethod
    def null_event(data: dict, **kwargs):
        """A null debug event that does nothing but logs its kwargs and overwrites the data dict with the args."""
        LOGGER.debug(
            "Null event received by pipeline data block %s with kwargs: %s",
            data["blocktype"],
            kwargs,
        )
        data["kwargs"] = kwargs["kwargs"]

    def add_parser(self, parser_function: ParserStage | Any) -> None:
        self.add_parsers([parser_function])

    def add_parsers(self, parser_functions: list[ParserStage] | Any) -> None:
        if self.parser_functions is None:
            self.parser_functions = []
        self.parser_functions.extend(parser_functions)

    def add_processor(self, processor_function: ProcessorStage) -> None:
        if self.processor_functions is None:
            self.processor_functions = []
        self.processor_functions.append([processor_function])

    def add_stage_of_processors(self, processor_functions: list[ProcessorStage]) -> None:
        if self.processor_functions is None:
            self.processor_functions = []
        self.processor_functions.append(processor_functions)

    def set_plotter(self, plotter_function: PlotterStage) -> None:
        self.plotter_function = plotter_function

    def set_caching_for_entire_pipeline(self, caching: bool) -> None:
        for parser in self.parser_functions:
            parser.caching = caching
        for stages in self.processor_functions:
            for processor in stages:
                processor.caching = caching

    def exists(self):
        return self.plotter_function or self.processor_functions or self.parser_functions

    def __init__(self, parser=None, processor=None, plotter=None, events=None):
        if not parser:
            # TODO default parser
            parser = []
            pass
        if not processor:
            processor = ProcessorStage(lambda df: df, list_df_input=False)
        if not plotter:
            plotter = PlotterStage(self.plotter)

        self.parser_functions = []
        self.processor_functions = []
        self.event_functions = {}

        # Check types and assign to pipeline
        if type(parser) is ParserStage:
            parser = [parser]
        if isinstance(processor, ProcessorStage):
            self.add_processor(processor)
        else:
            self.processor_functions = processor
        self.add_parsers(parser)
        self.set_plotter(plotter)
        if events:
            self.event_functions = events
        if "null_event" not in self.event_functions:
            self.event_functions["null_event"] = EventStage(self.null_event)

    def perform_entire_pipeline(
        self, data, file_folder: str | Path, files: list[Path | str], checksums: list[str]
    ):
        """
        Performs an entire complete pipeline with no caching or async operations.
        Used for both testing and single threaded pipelines where caching is not an option.
        """
        # set up computed and metadata fields
        data["metadata"] = {}
        data["computed"] = {}

        pipeline_graph: list[list[BlockStage]] = [self.parser_functions]
        pipeline_graph.extend(self.processor_functions)
        pipeline_graph.append([self.plotter_function])

        graph_output = OutputRoot()
        entry_point_leaves: list[FileInputLeaf] = graph_output.add_pipeline(pipeline_graph)
        for leaf in entry_point_leaves:
            leaf_files = []
            leaf_checksums = []
            for index in range(len(files) - 1, -1, -1):
                file = files[index]
                if Path(file).suffix in leaf.file_input_type or "*" in leaf.file_input_type:
                    leaf_files.append(Path(file))
                    leaf_checksums.append(checksums[index])
                    files.pop(index)
                    checksums.pop(index)
            leaf.register_files_and_execute(leaf_files, leaf_checksums, file_folder, data)
        result = graph_output.get_result()
        data = merge_dictionaries(data, result["data"])
        data["bokeh_plot_data"] = result.get("function_input", None)
        return data

    def clone(self) -> "pipeline":
        clone = copy.copy(self)
        clone.parser_functions = list(self.parser_functions)
        clone.processor_functions = [list(group) for group in self.processor_functions]
        clone.event_functions = dict(self.event_functions)
        return clone
