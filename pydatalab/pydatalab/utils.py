"""This module contains utility functions that can be used
anywhere in the package.

"""

import datetime
from math import ceil

import pandas as pd
from bson import json_util
from flask.json import JSONEncoder


def reduce_df_size(df: pd.DataFrame, target_nrows: int) -> pd.DataFrame:
    """Reduce the dataframe to the number of target rows by applying a stride.

    Parameters:
        df: The dataframe to reduce.
        target_nrows: The target number of rows to reduce each column to.

    Returns:
        A copy of the input dataframe with the applied stride.

    """
    return df.iloc[:: ceil(len(df) / target_nrows)].copy()


class CustomJSONEncoder(JSONEncoder):
    """Use a JSON encoder that can handle pymongo's bson."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime.datetime.isoformat(obj)
        return json_util.default(obj)
