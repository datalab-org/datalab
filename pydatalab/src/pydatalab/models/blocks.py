from pydantic import BaseModel

from pydatalab.models.utils import JSON_ENCODERS, PyObjectId


class DataBlockResponse(BaseModel):
    """A generic response model for a block, i.e., what is stored in `self.data`
    in the corresponding DataBlock class.
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

    b64_encoded_image: dict[PyObjectId, str] | None
    """Any base64-encoded image data associated with the block, keyed by file_id, if any."""

    bokeh_plot_data: dict | None
    """A JSON-encoded string containing the Bokeh plot data, if any."""

    processed_data: dict | None = None
    """Any processed data associated with the block, small enough to store."""

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "allow"
