"""This module contains utility functions that can be used
anywhere in the package.

"""

import datetime
from json import JSONEncoder
from math import ceil

import pandas as pd
from bson import json_util
from flask.json.provider import DefaultJSONProvider


def reduce_df_size(df: pd.DataFrame, target_nrows: int, endpoint: bool = True) -> pd.DataFrame:
    """Reduce the dataframe to the number of target rows by applying a stride.

    Parameters:
        df: The dataframe to reduce.
        target_nrows: The target number of rows to reduce each column to.
        endpoint: Whether to include the endpoint of the dataframe.

    Returns:
        A copy of the input dataframe with the applied stride.

    """
    num_rows = len(df)
    stride = ceil(num_rows / target_nrows)
    if endpoint:
        indices = [0] + list(range(stride, num_rows - 1, stride)) + [num_rows - 1]
    else:
        indices = list(range(0, num_rows, stride))

    return df.iloc[indices].copy()


class CustomJSONEncoder(JSONEncoder):
    """A custom JSON encoder that uses isoformat datetime strings and
    BSON for other serialization."""

    @staticmethod
    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

        return json_util.default(o)


class BSONProvider(DefaultJSONProvider):
    """A custom JSON provider that uses isoformat datetime strings and
    BSON for other serialization."""

    @staticmethod
    def default(o):
        return CustomJSONEncoder.default(o)


def shrink_label(label: str | None, max_length: int = 10) -> str:
    """Shrink label to exactly max_length chars with format: start...end.ext"""
    if not label:
        return ""

    if len(label) <= max_length:
        return label

    if "." in label:
        name, ext = label.rsplit(".", 1)

        extension_length = len(ext) + 1

        available_for_start = max_length - extension_length - 4

        if available_for_start >= 1:
            name_start = name[:available_for_start]
            last_char = name[-1]
            return f"{name_start}...{last_char}.{ext}"
        else:
            name_start = name[0]
            last_char = name[-1]
            return f"{name_start}...{last_char}.{ext}"
    else:
        return label[: max_length - 3] + "..."
