from pydantic import BaseModel, Field

from pydatalab.models.utils import JSON_ENCODERS, PyObjectId


class DataBlockResponse(BaseModel):
    """A generic response model for a block, i.e., what is stored in `self.data`
    in the corresponding DataBlock class.

    It is expected but not mandatory that this model will be extended by the specific block type
    where possible.
    """

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
        datalab_exclude_from_db=True, datalab_exclude_from_load=True
    )
    """Any base64-encoded image data associated with the block, keyed by `file_id`."""

    bokeh_plot_data: dict | None = Field(
        datalab_exclude_from_db=True, datalab_exclude_from_load=True
    )
    """A JSON-encoded string containing the Bokeh plot data, if any."""

    computed: dict | None = Field(default=None, datalab_exclude_from_load=True)
    """Any processed or computed data associated with the block, small enough to store and filter directly in the database,
    i.e., strings or a few hundred numbers not exceeding 16KB in size.
    Examples could include peak positions, and widths, but not the full spectrum.
    """

    metadata: dict | None = Field(default=None, datalab_exclude_from_load=True)
    """Any structured metadata associated with the block, for example,
    experimental acquisition parameters."""

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "allow"
