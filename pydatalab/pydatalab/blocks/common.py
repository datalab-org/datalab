import base64
import io
import warnings

import pandas as pd
from PIL import Image

from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .base import DataBlock


class NotSupportedBlock(DataBlock):
    blocktype = "notsupported"
    description = "Block not supported"
    _supports_collections = True


class CommentBlock(DataBlock):
    blocktype = "comment"
    description = "Comment"
    _supports_collections = True


class MediaBlock(DataBlock):
    blocktype = "media"
    description = "Media"
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


class PlotterBlock(DataBlock):
    """This block simply tries to read the given file with pandas, and
    expose an interface to plot its columns as scatter points.

    """

    blocktype = "plotter"
    description = "Simple Plot"
    accepted_file_extensions = (".csv", ".txt", ".tsv", ".dat")

    @property
    def plot_functions(self):
        return (self.plot_df,)

    def _load(self) -> pd.DataFrame:
        if "file_id" not in self.data:
            warnings.warn(
                f"{self.__class__.__name__}.read_data_file(): No file set in the DataBlock"
            )
            return

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

        try:
            return pd.read_csv(file_info["location"], sep=None, skip_blank_lines=False)
        except Exception as e:
            raise RuntimeError(f"`pandas.read_csv()` was not able to read the file. Error: {e}")

    def plot_df(self):
        import bokeh.embed

        from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot

        LOGGER.debug("Reached here.")

        df = self._load()
        if df is None:
            return
        columns = list(df.columns)
        LOGGER.debug("Reached here 2.")
        plot = selectable_axes_plot(
            df,
            x_options=columns,
            y_options=columns,
            # color_options=columns,
            x_default=columns[0],
            y_default=columns[1],
            plot_points=True,
            plot_line=False,
        )

        LOGGER.debug("Reached here 3.")

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)
