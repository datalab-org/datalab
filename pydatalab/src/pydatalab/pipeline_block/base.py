import pprint
import traceback
import warnings
from pathlib import Path
from typing import Any

import bokeh.embed
import pandas as pd

from pydatalab import __version__
from pydatalab.config import CONFIG
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.models.blocks import DataBlockResponse
from pydatalab.pipeline_block.block_stage import (
    EventStage,
    ParserStage,
    PlotterStage,
    ProcessorStage,
)

__all__ = ("PipelineDataBlock",)

from pydatalab.pipeline_block.utils import generate_random_id


class MetaPipelineDataBlock(type):
    name: str = "base"
    """The human-readable block name specifying which technique
    or file format it pertains to.
    """

    blocktype: str = "generic pipeline"
    """A short (unique) string key specifying the type of block."""

    description: str = "Generic pipeline Block"
    """A longer description outlining the purpose and capability
    of the block."""

    accepted_file_extensions: tuple[str, ...] | None = ()
    """A list of file extensions that the block will attempt to read."""

    defaults: dict[str, Any] = {}
    """Any default values that should be set if they are not
    supplied during block init.
    """

    multi_file: bool = False
    """Whether this block can accept multiple files as input."""

    parser_functions: list[ParserStage]
    """A list of methods that will parse files for this datablock."""

    processor_functions: list[list[ProcessorStage]]
    """A list of processor stages that will operate on the data for this datablock."""

    plotter_function: PlotterStage
    """ The plotter that will create the plot from the data in this datablock."""

    event_functions: dict[str, EventStage]
    """ The event stage functions, used when calling an event for a partial parameter update """

    @staticmethod
    def processor(df: pd.DataFrame, data: dict | None) -> pd.DataFrame:
        return df

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

    def __init__(
        cls,
        name,
        bases,
        namespace,
        *,
        parser: ParserStage | list[ParserStage] | None = None,
        processor: ProcessorStage | list[list[ProcessorStage]] | None = None,
        plotter: PlotterStage | None = None,
        events: dict[str, EventStage] | None = None,
        blocktype: str | None = blocktype,
        block_name: str | None = name,
        description: str | None = description,
        accepted_file_extensions: tuple[str, ...] | None = accepted_file_extensions,
        multi_file: bool = multi_file,
        defaults=None,
    ):
        super().__init__(cls)

        # Set variables here
        if defaults is None:
            defaults = {}
        cls.name = namespace.get("name", block_name)
        cls.description = namespace.get("description", description)
        cls.accepted_file_extensions = namespace.get(
            "accepted_file_extensions", accepted_file_extensions
        )
        cls.blocktype = namespace.get("blocktype", blocktype)
        cls.multi_file = namespace.get("multi_file", multi_file)
        cls.defaults = namespace.get("defaults", defaults)

        parser = namespace.get("parser", parser)
        processor = namespace.get("processor", processor)
        plotter = namespace.get("plotter", plotter)

        # Set default default pipeline stages
        if not parser:
            # TODO default parser
            parser = []
            pass
        if not processor:
            processor = ProcessorStage(cls.processor, list_df_input=False)
        if not plotter:
            plotter = PlotterStage(cls.plotter)

        cls.parser_functions = []
        cls.processor_functions = []
        cls.event_functions = {}

        # Check types and assign to pipeline
        if type(parser) is ParserStage:
            parser = [parser]
        if isinstance(processor, ProcessorStage):
            cls.add_processor(processor)
        else:
            cls.processor_functions = processor
        cls.add_parsers(parser)
        cls.set_plotter(plotter)
        if events:
            cls.event_functions = events
        if "null_event" not in cls.event_functions:
            cls.event_functions["null_event"] = EventStage(cls.null_event)


class PipelineDataBlock(metaclass=MetaPipelineDataBlock):
    name: str = "base"
    """The human-readable block name specifying which technique
    or file format it pertains to.
    """

    blocktype: str = "generic pipeline"
    """A short (unique) string key specifying the type of block."""

    description: str = "Generic pipeline Block"
    """A longer description outlining the purpose and capability
    of the block."""

    accepted_file_extensions: tuple[str, ...] | None = ()
    """A list of file extensions that the block will attempt to read."""

    defaults: dict[str, Any] = {}
    """Any default values that should be set if they are not
    supplied during block init.
    """

    multi_file: bool = False
    """Whether this block can accept multiple files as input."""

    block_db_model = DataBlockResponse
    """Base class for a data block. Has a metaclass of MetaPipelineDataBlock."""
    version: str = __version__
    """The implementation version of this particular block."""

    parser_functions: list[ParserStage]
    """A list of methods that will parse files for this datablock."""

    processor_functions: list[list[ProcessorStage]]
    """A list of processor stages that will operate on the data for this datablock."""

    plotter_function: PlotterStage
    """ The plotter that will create the plot from the data in this datablock."""

    event_functions: dict[str, EventStage]
    """ The event stage functions, used when calling an event for a partial parameter update """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def __init__(
        self,
        item_id: str | None = None,
        init_data: dict | None = None,
        unique_id: str | None = None,
    ):
        """Create a data block object for the given `item_id` or `collection_id`.

        Parameters:
            item_id: The item to which the block is attached, or
            init_data: A dictionary of data to initialise the block with.
            unique_id: A unique id for the block, used in the DOM and database.

        """
        if init_data is None:
            init_data = {}

        if item_id is None:
            raise RuntimeError(f"Must supply `item_id` to make {self.__class__.__name__}.")

        LOGGER.debug(
            "Creating new block '%s' associated with item_id '%s'",
            self.__class__.__name__,
            item_id,
        )
        self.block_id = (
            unique_id or generate_random_id()
        )  # this is supposed to be a unique id for use in html and the database.
        self.data = {
            "item_id": item_id,
            "blocktype": self.blocktype,
            "block_id": self.block_id,
            **self.defaults,
        }

        # convert ObjectId file_ids to string to make handling them easier when sending to and from web
        if "file_id" in self.data:
            self.data["file_id"] = str(self.data["file_id"])

        if "title" not in self.data:
            self.data["title"] = self.name
        self.data.update(
            init_data
        )  # this could overwrite blocktype and block_id. I think that's reasonable... maybe
        LOGGER.debug(
            "Initialised block %s for item ID %s",
            self.__class__.__name__,
            item_id,
        )

    def to_db(self) -> dict:
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""

        LOGGER.debug("Casting block %s to database object.", self.__class__.__name__)
        exclude_fields: set[str] = {
            f
            for (f, s) in self.block_db_model.model_json_schema()["properties"].items()
            if s.get("datalab_exclude_from_db")
        }
        return self.block_db_model(**self.data).model_dump(
            exclude=exclude_fields,
            exclude_unset=True,
            exclude_none=True,
        )

    def perform_entire_pipeline(self):
        """
        Performs an entire complete pipeline with no caching or async operations.
        Used for both testing and single threaded pipelines where caching is not an option.
        """
        # First step - retrieve the file(s)
        if ("file_id" not in self.data and not self.multi_file) or (
            "file_ids" not in self.data and self.multi_file
        ):
            LOGGER.warning("No file(s) set in the DataBlock")
            return

        file_ids: list[str] = []

        # Case one: multiple files
        if "file_ids" in self.data:
            file_ids = self.data["file_ids"]
        # Case two: single file
        elif "file_id" in self.data:
            file_ids = [self.data["file_id"]]

        if len(file_ids) == 0:
            return

        files: list[Path] = []
        checksums: list[str] = []

        # Check extension and append the Path object into a list
        for file_id in file_ids:
            try:
                file_info = get_file_info_by_id(file_id, update_if_live=True)
            except OSError:
                LOGGER.warning("Missing file found in database but no on disk: %s", file_id)
            else:
                ext = Path(file_info["location"]).suffix
                if ext not in self.accepted_file_extensions:
                    LOGGER.warning(
                        "File with extension `%s` is not an acceptable file extension, (acceptable parsers: `%s`)",
                        ext,
                        self.accepted_file_extensions,
                    )
                    return
                files.append(Path(file_info["location"]))
                checksums.append(file_info["checksums"])

        # Second step - pass through parser(s)
        file_folder = CONFIG.FILE_DIRECTORY
        parser_output_df: "list[pd.DataFrame]" = []
        parser_checksums: list[str] = []

        for index, file in enumerate(files):
            # TODO Need to refactor in case we want to parse two .txt(/any other extension) files that are the same..
            # TODO logic could also do with refining, depending on use case.
            for parser in self.parser_functions:
                LOGGER.info("Processing file %s", file)
                try:
                    parser_checksum, result = parser.perform_with_cache(
                        checksums[index], file_folder, file
                    )
                except Exception as exc:
                    warnings.warn(
                        f"Could not parse file {file} as {self.blocktype} data. Error: {exc}"
                    )
                else:
                    if result is not None:
                        parser_output_df.append(result)
                        parser_checksums.append(parser_checksum)
                        break
            else:
                LOGGER.warning(
                    "This file failed to be processed successfully by any of the available parsers"
                )
        # Third step - pass through the processors
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
                    process_checksum, result = processor.perform_with_cache(
                        "".join(processor_checksums), file_folder, processor_input, **self.data
                    )
                    if result:
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
                    LOGGER.info(processor)
                    process_checksum, result = processor.perform_with_cache(
                        processor_checksums[i], file_folder, processor_input[i], **self.data
                    )
                    if result:
                        if type(result) is not list:
                            result = [result]
                        processor_output.extend(result)
                        output_checksums.extend([process_checksum] * len(result))
            # Reset variables for next iteration
            processor_input_name = f"output from layer {ind}"
            processor_input = processor_output
            processor_checksums = output_checksums

        # Fourth step - plot
        if len(processor_output) == 0:
            LOGGER.info("There is no dataframe to plot, processors are most presumably malformed")
        elif len(processor_output) > 1 and not self.plotter_function.list_df_input:
            LOGGER.warning(
                "There is not one sole dataframe to plot (len = %s) and the plotter does not support multiple dataframe, "
                "processors are most presumably malformed.",
                len(processor_output),
            )
        elif not self.plotter_function.list_df_input:
            self.data["bokeh_plot_data"] = self.plotter_function.perform(
                processor_output[0], **self.data
            )
        else:
            self.data["bokeh_plot_data"] = self.plotter_function.perform(
                processor_output, **self.data
            )

    def to_web(self) -> dict[str, Any]:
        """Returns a JSON serializable dictionary to render the data block on the web."""
        block_errors = []
        block_warnings = []
        if self.plotter_function or self.processor_functions or self.parser_functions:
            with warnings.catch_warnings(record=True) as captured_warnings:
                try:
                    self.perform_entire_pipeline()
                except Exception as e:
                    tb_list = traceback.extract_tb(e.__traceback__)
                    last = tb_list[-1]
                    block_errors.append(f"{self.__class__.__name__} raised error: {e}")
                    LOGGER.warning(
                        "Could not create plot for %s due to error at %s:%s in %s → %r:\n\t%s: %s",
                        self.__class__.__name__,
                        last.filename,
                        last.lineno,
                        last.name,
                        last.line,
                        type(e).__name__,
                        e,
                    )
                    LOGGER.debug(
                        "The full data for the errored block is:\n%s",
                        pprint.pformat(self.data),
                    )
                finally:
                    if captured_warnings:
                        block_warnings.extend(
                            [
                                f"{self.__class__.__name__} raised warning: {w.message}"
                                for w in captured_warnings
                            ]
                        )

        # If the last plotting run did not raise any errors or warnings, remove any old ones
        if block_errors:
            self.data["errors"] = block_errors
        else:
            self.data.pop("errors", None)
        if block_warnings:
            self.data["warnings"] = block_warnings
        else:
            self.data.pop("warnings", None)
        LOGGER.info(str(self.data))

        return self.block_db_model(**self.data).model_dump(exclude_unset=True, exclude_none=True)

    def process_events(self, events: list[dict] | dict):
        """Handle any supported events passed to the block."""
        if isinstance(events, dict):
            events = [events]

        for event in events:
            # Match the event to any registered by the block
            if (event_name := event.pop("event_name")) in self.event_functions.keys():
                # Bind the method to the instance before calling
                event_stage = self.event_functions[event_name]
                try:
                    event_stage.perform(self.data, **event)
                except Exception as e:
                    LOGGER.error(
                        "Error processing event %s for block %s: %s",
                        event_name,
                        self.__class__.__name__,
                        e,
                    )
                    self.data["errors"] = [
                        f"{self.__class__.__name__}: Error processing event {event}: {e}"
                    ]

    @classmethod
    def from_web(cls, data: dict):
        """Initialise the block state from data passed via web request
        with a given item, collection and block ID.

        Parameters:
            data: The block data to initialise the block with.
        """
        block = cls(
            item_id=data.get("item_id"),
            unique_id=data["block_id"],
        )
        block.update_from_web(data)
        return block

    def update_from_web(self, data: dict):
        """Update the block with validated data received from a web request.
        Will strip any fields that are "computed" or otherwise not controllable
        by the user.

        Parameters:
            data: A dictionary of data to update the block with.
        """
        LOGGER.debug(
            "Updating block %s from web request",
            self.__class__.__name__,
        )
        exclude_fields: set[str] = {
            f
            for (f, s) in self.block_db_model.model_json_schema()["properties"].items()
            if s.get("datalab_exclude_from_load")
        }
        [data.pop(f, None) for f in exclude_fields]
        self.data.update(self.block_db_model(**data).model_dump(exclude_unset=True))
        return self

    @staticmethod
    def define(
        class_name: str,
        *,
        parser: ParserStage | list[ParserStage] | None = None,
        processor: ProcessorStage | list[list[ProcessorStage]] | None = None,
        plotter: PlotterStage | None = None,
        events: dict[str, EventStage] | None = None,
        blocktype: str | None = None,
        name: str | None = None,
        description: str | None = None,
        accepted_file_extensions: tuple[str, ...] | None = None,
        multi_file: bool = False,
        defaults: dict[str, Any] | None = None,
    ):
        return MetaPipelineDataBlock(
            class_name,
            (PipelineDataBlock,),
            {},
            parser=parser,
            processor=processor,
            plotter=plotter,
            events=events,
            blocktype=blocktype,
            block_name=name,
            description=description,
            accepted_file_extensions=accepted_file_extensions,
            multi_file=multi_file,
            defaults=defaults,
        )
