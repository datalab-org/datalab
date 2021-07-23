"""This module contains utility functions that can be used
anywhere in the package.

"""

from math import ceil

import pandas as pd


def reduce_df_size(df: pd.DataFrame, target_nrows: int) -> pd.DataFrame:
    """Reduce the dataframe to the number of target rows by applying a stride.

    Parameters:
        df: The dataframe to reduce.
        target_nrows: The target number of rows to reduce each column to.

    Returns:
        A copy of the input dataframe with the applied stride.

    """
    return df.iloc[:: ceil(len(df) / target_nrows)].copy()
