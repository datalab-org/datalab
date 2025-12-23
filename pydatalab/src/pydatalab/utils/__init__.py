"""This module contains utility functions that can be used
anywhere in the package.

"""

import datetime
from json import JSONEncoder
from math import ceil

import pandas as pd
from bson import ObjectId
from flask.json.provider import DefaultJSONProvider

__all__ = ("reduce_df_size", "CustomJSONEncoder", "BSONProvider")


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

        elif isinstance(o, ObjectId):
            return str(o)

        raise RuntimeError(f"Type {type(o)} not serializable")


class BSONProvider(DefaultJSONProvider):
    """A custom JSON provider that uses isoformat datetime strings and
    BSON for other serialization."""

    @staticmethod
    def default(o):
        return CustomJSONEncoder.default(o)
