import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from .base import DataBlockDefaults
from .block_stages import ParserStage
from .pipeline import Pipeline

if TYPE_CHECKING:
    import pandas as pd


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

TabularDefaults = DataBlockDefaults(
    blocktype=blocktype,
    name=name,
    description=description,
    accepted_file_extensions=accepted_file_extensions,
    multi_file=False,
)
tabular_pipeline = Pipeline(
    parser=[ParserStage(load_excel, list(EXCEL_LIKE_EXTENSIONS)), ParserStage(load_other, "*")]
)

TABULAR_DATABLOCK = {
    "pipeline": tabular_pipeline,
    "default_params": TabularDefaults,
}
