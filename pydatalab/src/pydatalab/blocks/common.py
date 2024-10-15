import base64
import io
import warnings
from pathlib import Path

import pandas as pd
from PIL import Image

from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .base import DataBlock


class NotSupportedBlock(DataBlock):
    name = "Not Supported"
    blocktype = "notsupported"
    description = "A placeholder block type when the requested block is not supported by the current version of the server."


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


class TabularDataBlock(DataBlock):
    """This block simply tries to read the given file with pandas, and
    expose an interface to plot its columns as scatter points.

    """

    blocktype = "tabular"
    name = "Tabular Data Block"
    description = "This block will load tabular data from common plain text files and allow you to create simple scatter plots of the columns within."
    accepted_file_extensions = (".csv", ".txt", ".tsv", ".dat")

    @property
    def plot_functions(self):
        return (self.plot_df,)

    def _load(self) -> pd.DataFrame:
        if "file_id" not in self.data:
            return

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

        return self.load(file_info["location"])

    @classmethod
    def load(cls, location: Path) -> pd.DataFrame:
        try:
            df = pd.read_csv(
                location,
                sep=None,
                encoding_errors="backslashreplace",
                skip_blank_lines=False,
                engine="python",
            )

            if df.isnull().values.any():
                warnings.warn(
                    f"Loading file with less strict parser: columns were previously detected as {df.columns}"
                )
                df = pd.read_csv(
                    location,
                    sep=None,
                    names=range(df.shape[1]),
                    comment="#",
                    header=None,
                    encoding_errors="backslashreplace",
                    skip_blank_lines=False,
                    engine="python",
                )
                # Drop a row if entirety is NaN
                df.dropna(axis=1, inplace=True)
        except Exception as e:
            raise RuntimeError(f"`pandas.read_csv()` was not able to read the file. Error: {e}")

        return df

    def plot_df(self):
        import bokeh.embed

        from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot

        df = self._load()
        if df is None:
            return
        columns = list(df.columns)
        plot = selectable_axes_plot(
            df,
            x_options=columns,
            y_options=columns,
            x_default=columns[0],
            y_default=columns[1],
            plot_points=True,
            plot_line=False,
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)
