"""This module contains utility functions that can be used
anywhere in the package.

"""

import datetime
from math import ceil

import pandas as pd
from bson import json_util
from flask.json import JSONEncoder


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
        indices = range(0, num_rows, stride)

    return df.iloc[indices].copy()


class CustomJSONEncoder(JSONEncoder):
    """Use a JSON encoder that can handle pymongo's bson."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime.datetime.isoformat(obj)
        return json_util.default(obj)
