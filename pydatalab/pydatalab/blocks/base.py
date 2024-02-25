import random
import warnings
from typing import Any, Callable, Optional, Sequence, Type

from pydantic import BaseModel

from pydatalab.logger import LOGGER
from pydatalab.models.utils import HumanReadableIdentifier, PyObjectId

__all__ = ("generate_random_id", "DataBlock")


def generate_random_id():
    """This function generates a random 15-length string for use as an id for a datablock. It
    should be sufficiently random that there is a negligible risk of ever generating
    the same id twice, so this is a unique id that can be used as a unique database refrence
    and also can be used as id in the DOM. Note: uuid.uuid4() would do this too, but I think
    the generated ids are too long and ugly.

    The ids here are HTML id friendly, using lowercase letters and numbers. The first character
    is always a letter.
    """
    randlist = [random.choice("abcdefghijklmnopqrstuvwxyz")] + random.choices(
        "abcdefghijklmnopqrstuvwxyz0123456789", k=14
    )
    return "".join(randlist)


class BlockMetadata(BaseModel):
    class Config:
        extra = "forbid"


class BlockDataModel(BaseModel):
    block_id: str
    blocktype: str
    title: str
    item_id: HumanReadableIdentifier | None = None
    collection_id: HumanReadableIdentifier | None = None
    file_id: PyObjectId | None | list[PyObjectId] = None
    bokeh_plot_data: Any | None = None
    metadata: BlockMetadata = BlockMetadata()
    errors: list[str] | None = None
    warnings: list[str] | None = None

    class Config:
        validate_assignment = True
        extra = "forbid"

    def to_db(self):
        return self.dict(exclude_none=True, exclude={"bokeh_plot_data"})


class DataBlock:
    """Base class for a data block."""

    block_id: str
    """The unique identifier for the block instance."""

    data_model: Type[BlockDataModel] = BlockDataModel

    data: BlockDataModel
    """The data model for the block.
    This is used to store the block's data and metadata in the database.
    """

    blocktype: str = "generic"
    """A unique identifier for the block type.
    This is used to determine which block class to use when loading from the database.
    """

    title: str = "Generic Block"
    """A short title for the block to be used in the UI.
    This can be overwritten per block instance by the user.
    """

    accepted_file_extensions: Sequence[str]
    """List of file extensions that this block can accept."""

    defaults: dict[str, Any] = {}
    """Used in the class definition to set default values for the block's metadata."""

    _supports_collections: bool = False
    """Whether this block supports being attached to a collection."""

    @property
    def plot_functions(self) -> Optional[Sequence[Callable[[], None]]]:
        return None

    def __init__(
        self,
        item_id: str | None = None,
        collection_id: str | None = None,
        block_id: str | None = None,
        dictionary: dict[str, Any] | None = None,
    ):
        """Initalises a block attached to an item or collection.

        If given, the `block_id` will be used as the unique identifier for this block,
        otherwise one will be generated.

        Will populate the `self.data` with the given defaults and dictionary
        metadata.

        Parameters:
            item_id: The unique identifier for the item that this block is attached to.
            collection_id: The unique identifier for the collection that this block is attached to.
            block_id: The unique identifier for this block instance.
            dictionary: A dictionary of data to populate the block with.

        """
        if dictionary is None:
            dictionary = {}

        if item_id is None and not self._supports_collections:
            raise RuntimeError(f"Must supply `item_id` to make {self.__class__.__name__}.")

        if collection_id is not None and not self._supports_collections:
            raise RuntimeError(
                f"This block ({self.__class__.__name__}) does not support collections."
            )

        if item_id is not None and collection_id is not None:
            raise RuntimeError("Must provide only one of `item_id` and `collection_id`.")

        LOGGER.debug(
            "Creating new block '%s' associated with item_id '%s'",
            self.__class__.__name__,
            item_id,
        )
        self.block_id: str = (
            block_id or generate_random_id()
        )  # this is supposed to be a unique id for use in html and the database.

        self.data = self.data_model(
            **{
                "block_id": self.block_id,
                "item_id": item_id,
                "collection_id": collection_id,
                "blocktype": self.blocktype,
                "title": self.title,
            }
        )

        for key in self.defaults:
            setattr(self.data.metadata, key, self.defaults[key])

        if "metadata" in dictionary:
            metadata = dictionary.pop("metadata")
            for key in metadata:
                setattr(self.data.metadata, key, metadata[key])

        for key in dictionary:
            setattr(self.data, key, dictionary[key])

        LOGGER.debug(
            "Initialised block %s for item ID %s or collection ID %s.",
            self.__class__.__name__,
            item_id,
            collection_id,
        )

    def to_db(self) -> dict[str, Any]:
        """Returns a dictionary with the data to store for this block."""
        return self.data.to_db()

    @classmethod
    def from_db(cls, db_entry: dict[str, Any]) -> "DataBlock":
        """Create a block from the stored database entry."""
        LOGGER.debug("Loading block %s from database object.", cls.__class__.__name__)
        return cls(
            item_id=db_entry.get("item_id"),
            collection_id=db_entry.get("collection_id"),
            dictionary=db_entry,
        )

    def to_web(self):
        """Return a JSON representation of the rendered block to serve through the API for use in the UI."""
        if self.plot_functions:
            self.data.errors = []
            self.data.warnings = []
            for plot in self.plot_functions:
                with warnings.catch_warnings(record=True) as captured_warnings:
                    try:
                        plot()
                    except Exception as e:
                        self.data.errors.append(f"{self.__class__.__name__} raised error: {e}")
                        LOGGER.warning(
                            f"Could not create plot for {self.__class__.__name__}: {self.data}"
                        )
                    finally:
                        if captured_warnings:
                            if not self.data.warnings:
                                self.data.warnings = []
                            self.data.warnings.extend(
                                [
                                    f"{self.__class__.__name__} raised warning: {w.message}"
                                    for w in captured_warnings
                                ]
                            )

        if not self.data.errors:
            self.data.errors = None
        if not self.data.warnings:
            self.data.warnings = None

        return self.data.dict()

    @classmethod
    def from_web(cls, data: dict[str, Any]) -> "DataBlock":
        """Create a block from the data received from a web request."""
        LOGGER.debug("Loading block %s from web request.", cls.__class__.__name__)
        return cls(
            item_id=data.get("item_id"),
            collection_id=data.get("collection_id"),
            block_id=data["block_id"],
            dictionary=data,
        )
