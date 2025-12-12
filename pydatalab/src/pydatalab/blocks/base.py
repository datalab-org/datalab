import functools
import pprint
import random
import traceback
import warnings
from collections.abc import Callable, Sequence
from typing import Any

from pydatalab import __version__
from pydatalab.logger import LOGGER
from pydatalab.models.blocks import DataBlockResponse

__all__ = ("generate_random_id", "DataBlock", "generate_js_callback_single_float_parameter")


def generate_js_callback_single_float_parameter(
    event_name: str, parameter: str, block_id: str, throttled: bool = False
) -> str:
    """Generates a Bokeh JS callback that can be attached
    to a widget and used to trigger datalab block events with
    a single named parameter.

    Parameters:
        event_name: The name of the block method to call.
        parameter: The name of the parameter to update.
        block_id: The ID of the block to target for the event.
        throttled: Whether to bind to the widget's `value` or `value_throttled`.

    """

    event_target: str = "event.target.value"
    if throttled:
        event_target += "_throttled"

    code = (
        r"""
const block_event = new CustomEvent('block-event', {
    detail: {
        block_id: '$block_id',
        event_name: '$event_name',
        $parameter: $event_target,
    }, bubbles: true
});
document.dispatchEvent(block_event);
""".replace("$event_name", event_name)
        .replace("$parameter", parameter)
        .replace("$event_target", event_target)
        .replace("$block_id", block_id)
    )
    return code.strip()


def event(func: Callable | None = None) -> Callable:
    """Decorator to register an event with a block."""

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Strip the block ID from the event if passed by the app
            kwargs.pop("block_id", None)
            return f(*args, **kwargs)

        wrapper._is_event = True
        return wrapper

    if func:
        return decorator(func)

    return decorator


class classproperty:
    """Decorator that creates a class-level property."""

    def __init__(self, method=None):
        self.method = method

    def __get__(self, instance, cls=None):
        return self.method(cls)


def generate_random_id():
    """This function generates a random 15-length string for use as an id for a datablock. It
    should be sufficiently random that there is a negligible risk of ever generating
    the same id twice, so this is a unique id that can be used as a unique database refrence
    and also can be used as id in the DOM. Note: uuid.uuid4() would do this too, but I think
    the generated ids are too long and ugly.

    The ids here are HTML id friendly, using lowercase letters and numbers. The first character
    is always a letter.
    """
    randlist = [random.choice("abcdefghijklmnopqrstuvwxyz")] + random.choices(  # noqa: S311
        "abcdefghijklmnopqrstuvwxyz0123456789", k=14
    )
    return "".join(randlist)


############################################################################################################
# Resources (base classes to be extended)
############################################################################################################


class DataBlock:
    """Base class for a data block."""

    block_db_model = DataBlockResponse

    name: str = "base"
    """The human-readable block name specifying which technique
    or file format it pertains to.
    """

    blocktype: str = "generic"
    """A short (unique) string key specifying the type of block."""

    description: str = "Generic Block"
    """A longer description outlining the purpose and capability
    of the block."""

    accepted_file_extensions: tuple[str, ...] | None
    """A list of file extensions that the block will attempt to read."""

    defaults: dict[str, Any] = {}
    """Any default values that should be set if they are not
    supplied during block init.
    """

    plot_functions: Sequence[Callable[[], None]] | None = None
    """A list of methods that will generate plots for this block."""

    _supports_collections: bool = False
    """Whether this datablock can operate on collection data, or just individual items"""

    version: str = __version__
    """The implementation version of this particular block."""

    def __init__(
        self,
        item_id: str | None = None,
        collection_id: str | None = None,
        init_data: dict | None = None,
        unique_id: str | None = None,
    ):
        """Create a data block object for the given `item_id` or `collection_id`.

        Parameters:
            item_id: The item to which the block is attached, or
            collection_id: The collection to which the block is attached.
            init_data: A dictionary of data to initialise the block with.
            unique_id: A unique id for the block, used in the DOM and database.

        """
        if init_data is None:
            init_data = {}

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
            self.data["title"] = self.name
        self.data.update(
            init_data
        )  # this could overwrite blocktype and block_id. I think that's reasonable... maybe
        LOGGER.debug(
            "Initialised block %s for item ID %s or collection ID %s.",
            self.__class__.__name__,
            item_id,
            collection_id,
        )

    def to_db(self) -> dict:
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""

        LOGGER.debug("Casting block %s to database object.", self.__class__.__name__)
        exclude_fields: set[str] = {
            f
            for (f, s) in self.block_db_model.schema()["properties"].items()
            if s.get("datalab_exclude_from_db")
        }
        return self.block_db_model(**self.data).dict(
            exclude=exclude_fields,
            exclude_unset=True,
            exclude_none=True,
        )

    def to_web(self) -> dict[str, Any]:
        """Returns a JSON serializable dictionary to render the data block on the web."""
        block_errors = []
        block_warnings = []
        if self.plot_functions:
            for plot in self.plot_functions:
                with warnings.catch_warnings(record=True) as captured_warnings:
                    try:
                        plot()
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

        return self.block_db_model(**self.data).dict(exclude_unset=True, exclude_none=True)

    def process_events(self, events: list[dict] | dict):
        """Handle any supported events passed to the block."""
        if isinstance(events, dict):
            events = [events]

        for event in events:
            # Match the event to any registered by the block
            if (event_name := event.pop("event_name")) in self.event_names:
                # Bind the method to the instance before calling
                bound_method = self.__class__.events_by_name[event_name].__get__(
                    self, self.__class__
                )
                try:
                    bound_method(**event)
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

    @event()
    def null_event(self, **kwargs):
        """A null debug event that does nothing but logs its kwargs and overwrites the data dict with the args."""
        LOGGER.debug(
            "Null event received by block %s with kwargs: %s", self.__class__.__name__, kwargs
        )
        self.data["kwargs"] = kwargs["kwargs"]

    @classmethod
    def _get_events(cls) -> dict[str, Callable]:
        events = {}
        # Loop over parent classes to find events
        for c in cls.__mro__:
            for name, method in c.__dict__.items():
                if hasattr(method, "_is_event"):
                    events[name] = method

        return events

    @classproperty
    def event_names(cls) -> set[str]:
        """Return a list of event names supported by this block."""
        return set(cls.events_by_name.keys())

    @classproperty
    def events_by_name(cls) -> dict[str, Callable]:
        """Returns a dict of registered events for this block."""
        return {
            name: method
            for name, method in cls._get_events().items()
            if getattr(method, "_is_event", False)
        }

    @classmethod
    def from_web(cls, data: dict):
        """Initialise the block state from data passed via web request
        with a given item, collection and block ID.

        Parameters:
            data: The block data to initialiaze the block with.

        """
        block = cls(
            item_id=data.get("item_id"),
            collection_id=data.get("collection_id"),
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
            for (f, s) in self.block_db_model.schema()["properties"].items()
            if s.get("datalab_exclude_from_load")
        }
        [data.pop(f, None) for f in exclude_fields]
        self.data.update(self.block_db_model(**data).dict())
        return self
