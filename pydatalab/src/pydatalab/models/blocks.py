from typing import Any, Literal

from pydantic import ConfigDict, Field

from pydatalab.models.entries import Entry
from pydatalab.models.traits import HasOwner, HasRevisionControl
from pydatalab.models.utils import BaseModel, PyObjectId


class DataBlockResponse(BaseModel):
    """A generic response model for a block, i.e., what is stored in `self.data`
    in the corresponding DataBlock class.

    It is expected but not mandatory that this model will be extended by the specific block type
    where possible.
    """

    model_config = ConfigDict(validate_by_name=True, extra="allow")

    blocktype: str
    """The type of the block."""

    block_id: str
    """A shorthand random ID for the block."""

    item_id: str | None = None
    """The item that the block is attached to, if any."""

    collection_id: str | None = None
    """The collection that the block is attached to, if any."""

    title: str | None = None
    """The title of the block, if any."""

    freeform_comment: str | None = None
    """A freeform comment for the block, if any."""

    file_id: PyObjectId | None = None
    """The ID of the file associated with the block, if any."""

    file_ids: list[PyObjectId] | None = None
    """A list of file IDs associated with the block, if any."""

    errors: list[str] | None = None
    """Any errors that occurred during block processing."""

    warnings: list[str] | None = None
    """Any warnings that occurred during block processing."""

    b64_encoded_image: dict[str, str] | None = Field(
        None,
        json_schema_extra={"datalab_exclude_from_db": True, "datalab_exclude_from_load": True},
    )
    """Any base64-encoded image data associated with the block, keyed by `file_id`."""

    bokeh_plot_data: dict | None = Field(
        None,
        json_schema_extra={"datalab_exclude_from_db": True, "datalab_exclude_from_load": True},
    )
    """A JSON-encoded string containing the Bokeh plot data, if any."""

    computed: dict | None = Field(
        default=None, json_schema_extra={"datalab_exclude_from_load": True}
    )
    """Any processed or computed data associated with the block, small enough to store and filter directly in the database,
    i.e., strings or a few hundred numbers not exceeding 16KB in size.
    Examples could include peak positions, and widths, but not the full spectrum.
    """

    processed: dict | None = Field(
        default=None, json_schema_extra={"datalab_exclude_from_load": True}
    )

    metadata: dict | None = Field(
        default=None, json_schema_extra={"datalab_exclude_from_load": True}
    )
    """Any structured metadata associated with the block, for example,
    experimental acquisition parameters."""


# Here to avoid circular import
class HasBlocks(BaseModel):
    blocks_obj: dict[str, DataBlockResponse] = Field({})
    """A mapping from block ID to block data."""

    display_order: list[str] = Field([])
    """The order in which to display block data in the UI."""


class Block(Entry, HasOwner, HasRevisionControl):
    """A model for a data block stored as its own document in the `blocks` collection.

    This is the persistence envelope around a block's payload (the output of
    `DataBlock.to_db()`, stored verbatim under `data`); the payload itself is
    described by `DataBlockResponse` and its per-block-type subclasses.
    """

    type: Literal["blocks"] = "blocks"

    block_id: str
    """The runtime-generated shorthand ID for the block, used as the key in the
    parent item's `blocks_obj`/`display_order` and in the DOM."""

    blocktype: str
    """A short string key specifying the type (technique) of the block."""

    data: dict[str, Any] = Field(default_factory=dict)
    """The block payload, exactly as produced by `DataBlock.to_db()`."""

    version: int = 0
    """The latest committed version number of this block in `block_versions`.

    A newly created block starts at 0, i.e., with no committed version; the first
    version is cut when an item version snapshot is next saved. Block creation
    does not create a versioned entry. Only when item is saved."""
