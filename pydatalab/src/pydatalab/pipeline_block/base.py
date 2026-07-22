import pprint
import traceback
import warnings
from pathlib import Path
from typing import Any

from pydatalab import __version__
from pydatalab.config import CONFIG
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.models.blocks import DataBlockResponse
from pydatalab.pipeline_block.block_stages import (
    EventStage,
    ParserStage,
    PlotterStage,
    ProcessorStage,
)
from pydatalab.pipeline_block.pipeline import Pipeline
from pydatalab.pipeline_block.utils import generate_random_id

__all__ = ("PipelineDataBlock",)


class PipelineDataBlock:
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

    pipeline: Pipeline = Pipeline()
    """Pipeline to object to run."""

    multi_file: bool = False
    """Whether this block can accept multiple files as input."""

    block_db_model = DataBlockResponse
    """Base class for a data block. Has a metaclass of MetaPipelineDataBlock."""
    version: str = __version__
    """The implementation version of this particular block."""

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
        self.pipeline = self.__class__.pipeline.clone()

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

    def perform_operations(self):
        # First step - retrieve the file(s)
        if "file_id" not in self.data or ("file_ids" not in self.data and self.multi_file):
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
        # Perform pipeline step
        self.data = self.pipeline.perform_entire_pipeline(
            data=self.data, file_folder=CONFIG.FILE_DIRECTORY, files=files, checksums=checksums
        )

    def to_web(self) -> dict[str, Any]:
        """Returns a JSON serializable dictionary to render the data block on the web."""
        block_errors = []
        block_warnings = []
        if self.pipeline.exists():
            with warnings.catch_warnings(record=True) as captured_warnings:
                try:
                    self.perform_operations()
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
            if (event_name := event.pop("event_name")) in self.pipeline.event_functions.keys():
                # Bind the method to the instance before calling
                event_stage = self.pipeline.event_functions[event_name]
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

    @classmethod
    def define(
        cls,
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
        return type(
            class_name,
            (cls,),
            {
                "pipeline": Pipeline(
                    parser=parser, processor=processor, plotter=plotter, events=events
                ),
                "blocktype": blocktype or cls.blocktype,
                "name": name or cls.name,
                "description": description or cls.description,
                "accepted_file_extensions": accepted_file_extensions
                or cls.accepted_file_extensions,
                "multi_file": multi_file or cls.multi_file,
                "defaults": defaults or {},
            },
        )
