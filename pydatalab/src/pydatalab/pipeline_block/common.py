import base64
import io
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import PipelineDataBlock
from .block_stages import ParserStage, PlotterStage, ProcessorStage

if TYPE_CHECKING:
    import pandas as pd


class NotSupportedBlockPipeline(PipelineDataBlock):
    name = "Not Supported Pipeline"
    blocktype = "notsupportedPipeline"
    description = "A placeholder block type when the requested block is not supported by the current version of the server."


CommentBlockPipeline = PipelineDataBlock.define(
    "CommentBlockPipeline",
    name="Comment Pipeline",
    blocktype="commentPipeline",
    description="Add a rich text comment to the document.",
)


def plot_functions(self):
    return (self.encode_tiff,)


def image_parser(location: Path | str) -> "pd.DataFrame":
    import pandas as _pd
    from PIL import Image

    df = _pd.DataFrame()

    im = Image.open(Path(location))
    with io.BytesIO() as f:
        im.save(f, format="PNG")
        f.seek(0)
        df["b64_encoded_image"] = _pd.Series([base64.b64encode(f.getvalue()).decode()])
    df["file_content"] = location
    df["file_id"] = location
    return df


def image_processor(df: "pd.DataFrame", data: "dict") -> "pd.DataFrame":
    import pandas as _pd

    if not data.get("b64_encoded_image"):
        data["b64_encoded_image"] = {}
    data["b64_encoded_image"][str(df["file_id"].item())] = df["b64_encoded_image"].item()
    return _pd.DataFrame()


image_accepted_file_extensions = (
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


def image_plotter(_: "pd.DataFrame") -> Any:
    return None


MediaBlock = PipelineDataBlock.define(
    "MediaBlock",
    name="Media",
    blocktype="media",
    description="Display an image or a video of a supported format.",
    accepted_file_extensions=image_accepted_file_extensions,
    processor=ProcessorStage(image_processor, list_df_input=False),
    plotter=PlotterStage(image_plotter),
    parser=ParserStage(image_parser, list(image_accepted_file_extensions)),
)


def load_excel(location: Path | str) -> "pd.DataFrame":
    """
    If an excel-like format, try to read it with `pandas.read_excel()`.
    Returns:
        pd.DataFrame: The loaded dataframe.
    """
    import pandas as _pd

    try:
        df_dict = _pd.read_excel(location, sheet_name=None)
    except Exception as e:
        raise RuntimeError(f"`pandas.read_excel()` was not able to read the file. Error: {e}")

    df = next(iter(df_dict.values()))
    if len(df_dict) > 1:
        warnings.warn(
            f"Found multiple sheets in spreadsheet file {df_dict.keys()}, only using the first one."
        )

    return df


def load_other(location: Path | str) -> "pd.DataFrame":
    """Throw several pandas readers at the target file.
    Then, try well-described formats such as JSON, Parquet and Feather.
    Otherwise, use decreasingly strict csv parsers until successful.

    Returns:
        pd.DataFrame: The loaded dataframe.

    """
    import pandas as _pd

    try:
        df = _pd.read_csv(
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
            df = _pd.read_csv(
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


blocktype = "tabularPipeline"
name = "Tabular Data Block Pipeline"
description = "This block will load tabular data from common plain text files and Excel-like spreadsheets and allow you to create simple scatter plots of the columns within."

EXCEL_LIKE_EXTENSIONS: tuple[str, ...] = (".xls", ".xlsx", ".xlsm", ".xlsb", ".odf", ".ods", ".odt")
"""A tuple of file extensions that are considered Excel-like formats."""

NORMAL_EXTENSIONS: tuple[str, ...] = (
    ".csv",
    ".txt",
    ".tsv",
    ".dat",
)
"""A tuple of file extensions that are considered Normal formats."""

accepted_file_extensions: tuple[str, ...] = (*NORMAL_EXTENSIONS, *EXCEL_LIKE_EXTENSIONS)

TabularPipelineDataBlock = PipelineDataBlock.define(
    "TabularPipelineDataBlock",
    parser=[
        ParserStage(load_excel, list(EXCEL_LIKE_EXTENSIONS)),
        ParserStage(load_other, list(NORMAL_EXTENSIONS)),
    ],
    blocktype=blocktype,
    name=name,
    description=description,
    accepted_file_extensions=accepted_file_extensions,
    multi_file=False,
)
