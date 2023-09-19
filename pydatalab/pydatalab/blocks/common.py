import base64
import io

from PIL import Image

from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .base import DataBlock


class CommentBlock(DataBlock):
    name = "Comment"
    blocktype = "comment"
    description = "Add a rich text comment to the document."
    _supports_collections = True


class MediaBlock(DataBlock):
    name = "Media"
    blocktype = "media"
    description = "Display an image or a video of a supported format."
    accepted_file_extensions = (".png", ".jpeg", ".jpg", ".tif", ".tiff", ".mp4", ".mov", ".webm")
    _supports_collections = False

    @property
    def plot_functions(self):
        return (self.encode_tiff,)

    def encode_tiff(self):
        if "file_id" not in self.data:
            LOGGER.warning("ImageBlock.encode_tiff(): No file set in the DataBlock")
            return
        if "b64_encoded_image" not in self.data:
            self.data["b64_encoded_image"] = {}
        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        if file_info["name"].endswith(".tif") or file_info["name"].endswith(".tiff"):
            im = Image.open(file_info["location"])
            LOGGER.warning("Making base64 encoding of tif")
            with io.BytesIO() as f:
                im.save(f, format="PNG")
                f.seek(0)
                self.data["b64_encoded_image"][self.data["file_id"]] = base64.b64encode(
                    f.getvalue()
                ).decode()
