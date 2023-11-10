# -*- coding: utf-8 -*-
"""
Parser code for PalmSens PSTrace exports
in CSV format.

@author: gh513 (Gabriela Horowitz)

"""


from pathlib import Path
from typing import Optional

import pandas as pd


def read_palmsens_csv(
    filename: str | Path,
) -> tuple[dict[str, pd.DataFrame] | None, dict[str, pd.DataFrame] | None]:
    """
    Loads experimental data from a CSV file exported by PSTrace,
    splits the DataFrame based on a specified keyword,
    and returns a dictionary containing the resulting DataFrames.

    Args:
        filename: Name of the CSV file

    Returns:
        A tuple of dictionaries containing DataFrames split based on the keyword
            it is normally any type of measurement in the first df, and EIS in the following ones

    """

    # Open the file to get the number of columns in each line
    encodings = ["utf-16-le", "utf-8"]
    # Try multiple common file encodings
    for file_encoding in encodings:
        try:
            with open(filename, "r", encoding=file_encoding) as temp_f:
                # Get the number of columns in each line
                col_counts = [len(_.split(",")) for _ in temp_f.readlines()]
                break
        except UnicodeDecodeError as exc:
            print(exc)
            continue
    else:
        raise RuntimeError(f"Could not decode the file with any of {encodings}.")

    # Generate column names (names will be 0, 1, 2, ..., maximum columns - 1)
    column_names = [i for i in range(0, max(col_counts))]

    # Read CSV file into a DataFrame
    df = pd.read_csv(filename, header=None, names=column_names, encoding=file_encoding)

    # Find the locations of the keyword "Measurement" in any column. The file only has that when an EIS measurement starts
    mask = df.apply(lambda row: row.astype(str).str.contains("Measurement"), axis=1)
    mask["Any"] = mask.any(axis=1)
    groups = mask["Any"].cumsum()

    # Split the DataFrame based on the keyword occurrences and drop columns with all NaN values
    split_dfs = {group: df[group == groups].dropna(axis=1, how="all") for group in groups.unique()}

    impedance_data = _extract_impedance_data(split_dfs)
    dc_data = _extract_DC_data(split_dfs)

    return impedance_data, dc_data


def _find_row(df: pd.DataFrame, keyword: str) -> int:
    """This function finds the index of a row containing a keyword.

    Args:
        df: DataFrame where we are searching
        keyword: the keyword it searches for.

    Returns:
        The index of the row containing the keyword.

    """

    return df[df.apply(lambda row: row.astype(str).str.contains(keyword)).any(axis=1)].index[0]


def _extract_impedance_data(
    split_dfs: dict[str, pd.DataFrame]
) -> Optional[dict[str, pd.DataFrame]]:
    """Formats the data extracted from split_dfs, filtering the data related
    to Impedance measurements.

    Args:
        split_dfs: A dictionary containing values as dataframes for different measurements,
            that are the result of the function `read_palmsens_csv`.

    Returns:
      impedance_dfs: A dictionary storing dataframes related to Impedance measurements,
        indexed by their respective keys, each containing the measurement name, date, and
        the actual data.

    """

    # Initialize a list to store keys of dataframes with 'freq / Hz'
    dfs_with_freq = []

    # Create a dictionary to hold dataframes with impedance measurements
    impedance_dfs = {}

    # Check if 'freq / Hz' exists in any dataframe, and append the key to a list
    for key, df in split_dfs.items():
        if df.apply(lambda row: row.astype(str).str.contains("freq / Hz")).any().any():
            # Reset the index of the dataframe
            df = split_dfs[key].reset_index(drop=True)
            dfs_with_freq.append(key)

            # Find the row index that contains 'Measurement' to find the name to use
            name_row = _find_row(df, "Measurement")
            new_name = df.iloc[name_row][1]

            # Find the row index that contains 'Date and time' for the date and time
            date_row = _find_row(df, "Date and time")
            date_time = df.iloc[date_row][1]

            # Find the index of the row containing the string 'freq / Hz' to use as df header
            freq_row = _find_row(df, "freq / Hz")
            df.columns = df.iloc[freq_row]

            # Remove the row that contains 'freq / Hz' and rows before it
            df = df.drop(freq_row).drop(index=range(0, freq_row))

            # Store the extracted information and data in the impedance_dfs dictionary
            impedance_dfs[f"EIS measurement {key}"] = {
                "Name": new_name,
                "Date and Time": date_time,
                "Data": df,
            }

    # Check if there are dataframes with 'freq / Hz'
    if not dfs_with_freq:
        return None

    return impedance_dfs


def _extract_DC_data(split_dfs: dict[str, pd.DataFrame]) -> Optional[dict[str, pd.DataFrame]]:
    """Extracts and formats DC (direct current) measurement data from a
    collection of DataFrames.

    Args:
        split_dfs: A dictionary containing DataFrames to process,
            comes from the funtion `read_palmsens_csv`.

    Returns:
        A dictionary of formatted DC measurement data.
    """

    dfs_DC_meas = []
    dc_data_present = False
    # Process each DataFrame in the input dictionary
    for key, df in split_dfs.items():
        # Check for the presence of 'Date and time measurement:', only present in dataframes of DC measurements
        if (
            df.apply(lambda row: row.astype(str).str.contains("Date and time measurement:"))
            .any()
            .any()
        ):
            dc_data_present = True
            # Reset the index of the dataframe
            df = split_dfs[key].reset_index(drop=True)

            # Find and remove the row index containing 'File date:' because it belongs to EIS measurements
            # it is an artifact of how the different dataframes were split by getdata(filename)
            row_filedate = _find_row(df, "File date:")
            df = df.drop(df.index[row_filedate])

            # Create a dictionary of DataFrames with two columns each
            # (each DC measurements only consists on 2 columns that can change in the magnitude measured
            # possible magnitudes: time(s), Voltage (V), Currrent (microA)
            dc_dfs = {
                f"DC measurement {int(i/2)}": df.iloc[:, i : i + 2]
                for i in range(0, df.shape[1], 2)
            }
    if dc_data_present:
        # Select the first DataFrame 'DC measurement 0' as example to find rows
        df = dc_dfs["DC measurement 0"]

        # Find the row index for date/time of measurement, name of measurement and units
        date_row = _find_row(df, "Date and time measurement:")
        name_row = date_row - 1
        units_row = date_row + 1

        # Process each DataFrame in the generated dictionary
        for key, df in dc_dfs.items():
            dfs_DC_meas.append(key)
            # Extract date and time information
            date_time = df.iloc[date_row, 1]
            new_name = df.iloc[name_row, 1]

            # Set column headers as the units row
            df.columns = df.iloc[units_row]
            df = df.drop(units_row).drop(index=range(0, units_row))
            df.dropna(how="all", inplace=True)

            # Store the extracted information and data in the 'DC_dfs' dictionary
            dc_dfs[key] = {"Name": new_name, "Date and Time": date_time, "Data": df}

        n = len(dfs_DC_meas)
        print(f"There are {n} direct current measurements")

    if not dfs_DC_meas:
        return None

    return dc_dfs
