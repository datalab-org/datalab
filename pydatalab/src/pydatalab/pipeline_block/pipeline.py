import copy
import warnings
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
        self, data, file_folder: str, files: list[Path | str], checksums: list[str]
    ):
        """
        Performs an entire complete pipeline with no caching or async operations.
        Used for both testing and single threaded pipelines where caching is not an option.
        """

        # First step - pass through parser(s)
        parser_checksums, parser_output_df = self.parser_pass_step(checksums, file_folder, files)
        # Second step - pass through the processors
        processor_output = self.processor_pass_step(
            data, file_folder, parser_checksums, parser_output_df
        )

        # Third step - plot
        if len(processor_output) == 0:
            LOGGER.info("There is no dataframe to plot, processors are most presumably malformed")
        elif len(processor_output) > 1 and not self.plotter_function.list_df_input:
            LOGGER.warning(
                "There is not one sole dataframe to plot (len = %s) and the plotter does not support multiple dataframe, "
                "processors are most presumably malformed.",
                len(processor_output),
            )
        elif not self.plotter_function.list_df_input:
            data["bokeh_plot_data"] = self.plotter_function.perform(processor_output[0], **data)
        else:
            data["bokeh_plot_data"] = self.plotter_function.perform(processor_output, **data)
        return data

    def parser_pass_step(
        self, checksums: list[str], file_folder: str, files: list[Path | str]
    ) -> tuple[list[str], list[DataFrame]]:
        parser_output_df: "list[pd.DataFrame]" = []
        parser_checksums: list[str] = []

        for index, file in enumerate(files):
            # TODO Need to refactor in case we want to parse two .txt(/any other extension) files that are the same..
            for parser in self.parser_functions:
                LOGGER.info("Processing file %s", file)
                try:
                    parser_checksum, result = parser.perform_with_optional_cache(
                        checksums[index],
                        file_folder,
                        file,
                    )
                except Exception as exc:
                    warnings.warn(f"Could not parse file {file} as data. Error: {exc}")
                else:
                    if result is not None:
                        if type(result) is not list:
                            result = [result]
                        parser_output_df.extend(result)
                        parser_checksums.append(parser_checksum)
                        break
            else:
                LOGGER.warning(
                    "This file failed to be processed successfully by any of the available parsers"
                )
        return parser_checksums, parser_output_df

    def processor_pass_step(
        self, data, file_folder: str, parser_checksums: list[str], parser_output_df: list[DataFrame]
    ) -> list[DataFrame]:
        processor_input_name: str = "files"
        processor_input: list[pd.DataFrame] = parser_output_df
        processor_output: list[pd.DataFrame] = []
        processor_checksums: list[str] = parser_checksums

        for ind, processor_group in enumerate(self.processor_functions):
            processor_output = []
            output_checksums: list[str] = []
            # Check the length of input compared to the number of processors available
            if len(processor_input) != len(processor_group):
                LOGGER.info(
                    "Different number of %s to available processors (%s!=%s). "
                    "Assume lists of dfs should be passed to each processor.",
                    processor_input_name,
                    len(processor_input),
                    len(processor_group),
                )
                for processor in processor_group:
                    process_checksum, result = processor.perform_with_optional_cache(
                        "".join(processor_checksums), file_folder, processor_input, **data
                    )
                    if result is not None:
                        if type(result) is not list:
                            result = [result]
                        processor_output.extend(result)
                        output_checksums.extend([process_checksum] * len(result))
            else:
                LOGGER.info(
                    "Exact match between processors and %s, "
                    "proceeding to perform one-to-one processing.",
                    processor_input_name,
                )
                for i, processor in enumerate(processor_group):
                    process_checksum, result = processor.perform_with_optional_cache(
                        processor_checksums[i], file_folder, processor_input[i], **data
                    )
                    if result is not None:
                        if type(result) is not list:
                            result = [result]
                        processor_output.extend(result)
                        output_checksums.extend([process_checksum] * len(result))
            # Reset variables for next iteration
            processor_input_name = f"output from layer {ind}"
            processor_input = processor_output
            processor_checksums = output_checksums
        return processor_output

    def clone(self) -> "Pipeline":
        clone = copy.copy(self)
        clone.parser_functions = list(self.parser_functions)
        clone.processor_functions = [list(group) for group in self.processor_functions]
        clone.event_functions = dict(self.event_functions)
        return clone
