import base64
import io
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from pydatalab.logger import LOGGER

from .base import DataBlock

EXCEL_LIKE_EXTENSIONS: tuple[str, ...] = (".xls", ".xlsx", ".xlsm", ".xlsb", ".odf", ".ods", ".odt")
"""A tuple of file extensions that are considered Excel-like formats."""


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
    accepted_file_extensions = (
        ".png",
        ".jpeg",
        ".jpg",
        ".tif",
        ".tiff",
        ".mp4",
        ".mov",
        ".webm",
        ".pdf",
        ".svg",
    )
    _supports_collections = False

    @property
    def plot_functions(self):
        return (self.encode_tiff,)

    def encode_tiff(self):
        from PIL import Image

        from pydatalab.file_utils import get_file_info_by_id

        if "file_id" not in self.data:
            LOGGER.warning("ImageBlock.encode_tiff(): No file set in the DataBlock")
            return
        if not self.data.get("b64_encoded_image"):
            self.data["b64_encoded_image"] = {}
        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
        if ext in (".tif", ".tiff"):
            im = Image.open(file_info["location"])
            with io.BytesIO() as f:
                im.save(f, format="PNG")
                f.seek(0)
                self.data["b64_encoded_image"][str(self.data["file_id"])] = base64.b64encode(
                    f.getvalue()
                ).decode()


class TabularDataBlock(DataBlock):
    """This block simply tries to read the given file with pandas, and
    expose an interface to plot its columns as scatter points.

    """

    blocktype = "tabular"
    name = "Tabular Data Block"
    description = "This block will load tabular data from common plain text files and Excel-like spreadsheets and allow you to create simple scatter plots of the columns within."
    accepted_file_extensions = (".csv", ".txt", ".tsv", ".dat", *EXCEL_LIKE_EXTENSIONS)

    @property
    def plot_functions(self):
        return (self.plot_df,)

    def _load(self) -> "pd.DataFrame":
        if "file_id" not in self.data:
            return
        from pydatalab.file_utils import get_file_info_by_id

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

        return self.load(file_info["location"])

    @classmethod
    def load(cls, location: Path | str) -> "pd.DataFrame":
        """Throw several pandas readers at the target file.

        If an excel-like format, try to read it with `pandas.read_excel()`.
        Then, try well-described formats such as JSON, Parquet and Feather.
        Otherwise, use decreasingly strict csv parsers until successful.

        Returns:
            pd.DataFrame: The loaded dataframe.

        """
        import pandas as pd

        if not isinstance(location, Path):
            location = Path(location)

        if location.suffix in EXCEL_LIKE_EXTENSIONS:
            try:
                df_dict = pd.read_excel(location, sheet_name=None)
            except Exception as e:
                raise RuntimeError(
                    f"`pandas.read_excel()` was not able to read the file. Error: {e}"
                )

            df = next(iter(df_dict.values()))
            if len(df_dict) > 1:
                warnings.warn(
                    f"Found multiple sheets in spreadsheet file {df_dict.keys()}, only using the first one."
                )

            return df

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
                    "Loading file with less strict parser: columns were previously detected as {df.columns}"
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
        plot = selectable_axes_plot(
            df,
            plot_points=True,
            plot_line=False,
            show_table=True,
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)
