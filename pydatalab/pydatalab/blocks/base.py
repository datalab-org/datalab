import random
import warnings
from typing import Any, Callable, Dict, Optional, Sequence

from bson import ObjectId

from pydatalab.logger import LOGGER

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


############################################################################################################
# Resources (base classes to be extended)
############################################################################################################


class DataBlock:
    """base class for a data block."""

    blocktype: str = "generic"
    description: str = "Generic Block"
    accepted_file_extensions: Sequence[str]
    # values that are set by default if they are not supplied by the dictionary in init()
    defaults: Dict[str, Any] = {}
    # values cached on the block instance for faster retrieval
    cache: Optional[Dict[str, Any]] = None
    plot_functions: Optional[Sequence[Callable[[], None]]] = None
    # whether this datablock can operate on collection data, or just individual items
    _supports_collections: bool = False

    def __init__(
        self,
        item_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        dictionary=None,
        unique_id=None,
    ):
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

        # Initialise cache
        self.cache = {}

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
            "collection_id": collection_id,
            "blocktype": self.blocktype,
            "block_id": self.block_id,
            **self.defaults,
        }

        # convert ObjectId file_ids to string to make handling them easier when sending to and from web
        if "file_id" in self.data:
            self.data["file_id"] = str(self.data["file_id"])

        if "title" not in self.data:
            self.data["title"] = self.description
        self.data.update(
            dictionary
        )  # this could overwrite blocktype and block_id. I think that's reasonable... maybe
        LOGGER.debug(
            "Initialised block %s for item ID %s or collection ID %s.",
            self.__class__.__name__,
            item_id,
            collection_id,
        )

    def to_db(self):
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""

        LOGGER.debug("Casting block %s to database object.", self.__class__.__name__)

        if "bokeh_plot_data" in self.data:
            self.data.pop("bokeh_plot_data")

        if "file_id" in self.data:
            dict_for_db = self.data.copy()  # gross, I know
            dict_for_db["file_id"] = ObjectId(dict_for_db["file_id"])
            return dict_for_db

        return self.data

    @classmethod
    def from_db(cls, db_entry):
        """create a block from json (dictionary) stored in a db"""
        LOGGER.debug("Loading block %s from database object.", cls.__class__.__name__)
        new_block = cls(
            item_id=db_entry.get("item_id"),
            collection_id=db_entry.get("collection_id"),
            dictionary=db_entry,
        )
        if "file_id" in new_block.data:
            new_block.data["file_id"] = str(new_block.data["file_id"])
        return new_block

    def to_web(self) -> Dict[str, Any]:
        """Returns a JSON serializable dictionary to render the data block on the web."""
        block_errors = []
        block_warnings = []
        if self.plot_functions:
            for plot in self.plot_functions:
                with warnings.catch_warnings(record=True) as captured_warnings:
                    try:
                        plot()
                    except Exception as e:
                        block_errors.append(f"{self.__class__.__name__} raised error: {e}")
                        LOGGER.warning(
                            f"Could not create plot for {self.__class__.__name__}: {self.data}"
                        )
                    finally:
                        if captured_warnings:
                            block_warnings.extend(
                                [
                                    f"{self.__class__.__name__} raised warning: {w.message}"
                                    for w in captured_warnings
                                ]
                            )

        if block_errors:
            self.data["errors"] = block_errors
        if warnings:
            self.data["warnings"] = block_warnings

        return self.data

    @classmethod
    def from_web(cls, data):
        LOGGER.debug("Loading block %s from web request.", cls.__class__.__name__)
        block = cls(
            item_id=data.get("item_id"),
            collection_id=data.get("collection_id"),
            unique_id=data["block_id"],
        )
        block.update_from_web(data)
        return block

    def update_from_web(self, data):
        """update the object with data received from the website. Only updates fields
        that are specified in the dictionary- other fields are left alone"""
        LOGGER.debug(
            "Updating block %s from web request",
            self.__class__.__name__,
        )
        self.data.update(data)

        return self
