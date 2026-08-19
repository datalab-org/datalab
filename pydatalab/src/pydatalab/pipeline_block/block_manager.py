import pprint
import traceback
import warnings
from pathlib import Path
from typing import Any

from pydatalab.config import CONFIG
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.pipeline_block.base import DataBlockDefaults
from pydatalab.pipeline_block.pipeline import Pipeline
from pydatalab.pipeline_block.utils import generate_random_id


def get_datablock_params(func):
    def wrapper(self, data: dict, *args, **kwargs):
        params = self._list_of_blocks.get(data["blocktype"], None)
        if params is None:
            LOGGER.warning("This block does not exist")
            return None
        else:
            return func(self, data, params, *args, **kwargs)

    return wrapper


def get_datablock_params_from_string(func):
    def wrapper(self, block_type: str, *args, **kwargs):
        params = self._list_of_blocks.get(block_type, None)
        if params is None:
            LOGGER.warning("This block does not exist")
            return None
        else:
            return func(self, params, *args, **kwargs)

    return wrapper


def get_pipeline_params(func):
    def wrapper(self, data: dict, *args, **kwargs):
        pipeline = self._list_of_pipelines.get(data.get("blocktype", None), None)
        if pipeline is None:
            LOGGER.warning("This pipeline does not exist")
            return None
        else:
            return func(self, data, pipeline, *args, **kwargs)

    return wrapper


def _perform_operations(block: DataBlockDefaults, pipeline: Pipeline, data: dict):
    """
    Performs the file selection logic for the pipeline and then calls the pipeline `perform_entire_pipeline`.
    :param block: The default parameters for the datablock.
    :param pipeline: The pipeline instance that operates on the block.
    :param data: The data for the datablock.
    :return: The new data for the datablock.
    """

    # First step - retrieve the file(s)
    if ("file_id" not in data) and ("file_ids" not in data):
        LOGGER.warning("No file(s) set in the DataBlock")
        return None

    file_ids: list[str] = []

    # Case one: multiple files
    if "file_ids" in data:
        file_ids = data["file_ids"]
    # Case two: single file
    elif "file_id" in data:
        file_ids = [data["file_id"]]

    if len(file_ids) == 0:
        return None

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
            if ext not in block.accepted_file_extensions:
                LOGGER.warning(
                    "File with extension `%s` is not an acceptable file extension, (acceptable parsers: `%s`)",
                    ext,
                    block.accepted_file_extensions,
                )
                return None
            files.append(Path(file_info["location"]))
            checksums.append(file_info["checksums"])
    # Perform pipeline step
    data = pipeline.perform_entire_pipeline(
        data=data, file_folder=CONFIG.FILE_DIRECTORY, files=files, checksums=checksums
    )
    return data


class PipelineBlockManager:
    def __init__(self):
        self._list_of_blocks: dict[str, DataBlockDefaults] = {}
        self._list_of_pipelines: dict[str, Pipeline] = {}

    def register_block(self, pipeline: Pipeline, default_params: DataBlockDefaults):
        """Registers a new block with the given default parameters and the given pipeline."""
        self._list_of_pipelines[default_params.blocktype] = pipeline
        self._list_of_blocks[default_params.blocktype] = default_params

    def __contains__(self, item: str) -> bool:
        return item in self._list_of_blocks and item in self._list_of_pipelines

    def get_block_items(self):
        return self._list_of_blocks.items()

    @get_datablock_params
    def prefers_async(self, _, block: DataBlockDefaults):
        return getattr(block, "_prefers_async", False)

    @get_datablock_params_from_string
    def create_block_data(
        self,
        block: DataBlockDefaults,
        item_id: str | None = None,
        init_data: dict | None = None,
        unique_id: str | None = None,
    ):
        """Create a data block object for the given `item_id` or `collection_id`.

        Parameters:
            block: The datablock default values.
            item_id: The item to which the block is attached, or
            init_data: A dictionary of data to initialise the block with.
            unique_id: A unique id for the block, used in the DOM and database.

        """
        if init_data is None:
            init_data = {}

        if item_id is None:
            raise RuntimeError(f"Must supply `item_id` to make {block.__class__.__name__}.")

        LOGGER.debug(
            "Creating new block '%s' associated with item_id '%s'",
            block.__class__.__name__,
            item_id,
        )
        block_id = (
            unique_id or generate_random_id()
        )  # this is supposed to be a unique id for use in HTML and the database.
        data = {
            "item_id": item_id,
            "blocktype": block.blocktype,
            "block_id": block_id,
            **block.defaults,
        }

        # convert ObjectId file_ids to string to make handling them easier when sending to and from web
        if "file_id" in data:
            data["file_id"] = str(data["file_id"])

        if "title" not in data:
            data["title"] = block.name
        data.update(
            init_data
        )  # this could overwrite blocktype and block_id. I think that's reasonable... maybe
        LOGGER.debug(
            "Initialised block %s for item ID %s",
            block.__class__.__name__,
            item_id,
        )
        return data

    @get_datablock_params
    def to_db(
        self,
        data,
        block: DataBlockDefaults,
    ) -> dict:
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""

        LOGGER.debug("Casting block %s to database object.", str)
        exclude_fields: set[str] = {
            f
            for (f, s) in block.block_db_model.model_json_schema()["properties"].items()
            if s.get("datalab_exclude_from_db")
        }
        return block.block_db_model(**data).model_dump(
            exclude=exclude_fields,
            exclude_unset=True,
            exclude_none=True,
        )

    @get_pipeline_params
    def process_events(self, data, pipeline, events: list[dict] | dict):
        """Handle any supported events passed to the block."""
        if isinstance(events, dict):
            events = [events]

        for event in events:
            # Match the event to any registered by the block
            if (event_name := event.pop("event_name")) in pipeline.event_functions.keys():
                # Bind the method to the instance before calling
                event_stage = pipeline.event_functions[event_name]
                try:
                    event_stage.perform(data, **event)
                except Exception as e:
                    LOGGER.error(
                        "Error processing event %s for block %s: %s",
                        event_name,
                        self.__class__.__name__,
                        e,
                    )
                    data["errors"] = [
                        f"{self.__class__.__name__}: Error processing event {event}: {e}"
                    ]
        return data

    def from_web(self, block_type: str, new_data: dict):
        """Initialise the block state from data passed via web request
        with a given item, collection and block ID.

        Parameters:
            :param new_data: The new block data to initialise the block with.
            :param block_type: The type of block to use
        """
        data = self.create_block_data(
            block_type,
            item_id=new_data.get("item_id"),
            unique_id=new_data["block_id"],
        )
        return self.update_from_web(data, new_data)

    @get_pipeline_params
    @get_datablock_params
    def to_web(self, data, block, pipeline) -> dict[str, Any]:
        """Returns a JSON serializable dictionary to render the data block on the web."""
        block_errors = []
        block_warnings = []
        new_data = None
        if pipeline.exists():
            with warnings.catch_warnings(record=True) as captured_warnings:
                try:
                    new_data = _perform_operations(block, pipeline, data)
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
                        pprint.pformat(data),
                    )
                finally:
                    if captured_warnings:
                        block_warnings.extend(
                            [
                                f"{self.__class__.__name__} raised warning: {w.message}"
                                for w in captured_warnings
                            ]
                        )
        if new_data is not None:
            data = new_data
        # If the last plotting run did not raise any errors or warnings, remove any old ones
        if block_errors:
            data["errors"] = block_errors
        else:
            data.pop("errors", None)
        if block_warnings:
            data["warnings"] = block_warnings
        else:
            data.pop("warnings", None)
        LOGGER.info(str(data))

        return block.block_db_model(**data).model_dump(exclude_unset=True, exclude_none=True)

    @get_datablock_params
    def update_from_web(self, block_data: dict, block, new_data: dict):
        """Update the block with validated data received from a web request.
        Will strip any fields that are "computed" or otherwise not controllable
        by the user.

        Parameters:
            :param new_data: New data to update the block with.
            :param block_data: The current block data.
            :param block: The current block default data.
        """
        LOGGER.debug(
            "Updating block %s from web request",
            self.__class__.__name__,
        )
        exclude_fields: set[str] = {
            f
            for (f, s) in block.block_db_model.model_json_schema()["properties"].items()
            if s.get("datalab_exclude_from_load")
        }
        [new_data.pop(f, None) for f in exclude_fields]
        block_data.update(block.block_db_model(**new_data).model_dump(exclude_unset=True))
        return block_data
