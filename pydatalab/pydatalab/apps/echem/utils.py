from typing import List, Optional

import navani.echem as ec
import numpy as np
import pandas as pd

from pydatalab.logger import LOGGER
from pydatalab.utils import reduce_df_size


def reduce_echem_cycle_sampling(df: pd.DataFrame, num_samples: int = 100) -> pd.DataFrame:
    """Reduce number of cycles to at most `num_samples` points per half cycle. Will
    keep the endpoint values of each half cycle.

    Parameters:
        df: The echem dataframe to reduce, which must have cycling data stored
            under a `"half cycle"` column.
        num_samples: The maximum number of sample points to include per cycle.

    Returns:
        The output dataframe.

    """

    return_df = pd.DataFrame([])

    for _, half_cycle in df.groupby("half cycle"):
        return_df = pd.concat([return_df, reduce_df_size(
            half_cycle, num_samples, endpoint=True)])

    return return_df


def compute_gpcl_differential(
    df: pd.DataFrame,
    mode: str = "dQ/dV",
    smoothing: bool = True,
    polynomial_spline: int = 3,
    s_spline: float = 1e-5,
    window_size_1: int = 101,
    window_size_2: int = 1001,
    polyorder_1: int = 5,
    polyorder_2: int = 5,
    use_normalized_capacity: bool = False,
) -> pd.DataFrame:
    """Compute differential dQ/dV or dV/dQ for the input dataframe.

    Args:
        df: The input dataframe containing the raw cycling data.
        mode: Either 'dQ/dV' or 'dV/dQ'. Invalid inputs will default to 'dQ/dV'.
        smoothing: Whether or not to apply additional smoothing to the output differential curve.
        polynomial_spline: The degree of the B-spline fit used by navani.
        s_spline: The smoothing parameter used by navani.
        window_size_1: The window size for the `savgol` filter when smoothing the capacity.
        window_size_2: The window size for the `savgol` filter when smoothing the final differential.
        polyorder_1: The polynomial order for the `savgol` filter when smoothing the capacity.
        polyorder_2: The polynomial order for the `savgol` filter when smoothing the final differential.

    Returns:
        A data frame containing the voltages, capacities and requested differential
        on the reduced cycle list.

    """
    if len(df) < 2:
        LOGGER.debug(
            f"compute_gpcl_differential called on dataframe with length {len(df)}, too small to calculate derivatives"
        )
        return df

    if mode.lower().replace("/", "") == "dvdq":
        y_label = "voltage (V)"
        x_label = "capacity (mAh/g)" if use_normalized_capacity else "capacity (mAh)"
        yp_label = "dV/dQ (V/mA)"
    else:
        y_label = "capacity (mAh/g)" if use_normalized_capacity else "capacity (mAh)"
        x_label = "voltage (V)"
        yp_label = "dQ/dV (mA/V)"

    smoothing_parameters = {
        "polynomial_spline": polynomial_spline,
        "s_spline": s_spline,
        "window_size_1": window_size_1 if window_size_1 % 2 else window_size_1 + 1,
        "window_size_2": window_size_2 if window_size_2 % 2 else window_size_2 + 1,
        "polyorder_1": polyorder_1,
        "polyorder_2": polyorder_2,
        "final_smooth": smoothing,
    }

    differential_df = pd.DataFrame()

    # Loop over distinct half cycles
    for cycle in df["half cycle"].unique():
        # Extract all segments corresponding to this half cycle index
        df_cycle = df[df["half cycle"] == cycle]

        # Compute the desired derivative
        try:
            x, yp, y = ec.dqdv_single_cycle(
                df_cycle[y_label], df_cycle[x_label], **smoothing_parameters
            )
        except TypeError as e:
            LOGGER.debug(
                f"""Calculating derivative {mode} of half_cycle {cycle} failed with the following error (likely it is a rest or voltage hold):
                 {e}
                Skipping derivative calculation for this half cycle."""
            )
            continue

        # Set up an array per cycle segment that stores the cycle and half-cycle index
        cycle_index = df_cycle["full cycle"].max()
        cycle_index_array = np.full(len(x), int(cycle_index), dtype=int)
        half_cycle_index_array = np.full(len(x), int(cycle), dtype=int)

        differential_df = pd.concat(
            [
                differential_df,
                pd.DataFrame(
                    {
                        x_label: x,
                        y_label: y,
                        yp_label: yp,
                        "full cycle": cycle_index_array,
                        "half cycle": half_cycle_index_array,
                    }
                ),
            ]
        )

    return differential_df


def filter_df_by_cycle_index(
    df: pd.DataFrame, cycle_list: Optional[List[int]] = None
) -> pd.DataFrame:
    """Filters the input dataframe by the chosen rows in the `cycle_list`.
    If `half_cycle` is a column in the df, it will be used for filtering,
    otherwise `cycle index` will be used.

    Args:
        df: The input dataframe to filter. Must have the column "half cycle".
        cycle_list: The provided list of cycle indices to keep.

    Returns:
        A dataframe with all the data for the selected cycles.

    """
    if cycle_list is None:
        return df

    cycle_list = sorted(i for i in cycle_list if i > 0)

    if "half cycle" not in df.columns:
        if "cycle index" not in df.columns:
            raise ValueError(
                "Input dataframe must have either 'half cycle' or 'cycle index' column"
            )

        if len(cycle_list) == 1 and max(cycle_list) > df["cycle index"].max():
            cycle_list[0] = df["cycle index"].max()
        return df[df["cycle index"].isin(i for i in cycle_list)]

    try:
        if len(cycle_list) == 1 and 2 * max(cycle_list) > df["half cycle"].max():
            cycle_list[0] = df["half cycle"].max() // 2
        half_cycles = [
            i
            for item in cycle_list
            for i in [max((2 * int(item)) - 1, df["half cycle"].min()), 2 * int(item)]
        ]
    except ValueError as exc:
        raise ValueError(
            f"Unable to parse `cycle_list` as integers: {cycle_list}. Error: {exc}"
        ) from exc
    return df[df["half cycle"].isin(half_cycles)]


def getdata(filename, file_encoding="utf-16 LE", verbose=False):
    """
    Loads experimental data from a CSV file, splits the DataFrame based on a specified keyword,
    and returns a dictionary containing the resulting DataFrames.

    Args:
    - filename (str): Name of the CSV file
    - file_encoding (str): Encoding type for the CSV file, default is 'utf-16 LE'

    Returns:
    - split_dfs (dict): Dictionary containing DataFrames split based on the keyword
      it is normally any type of measurement in the first df, and EIS in the following ones
    """

    # Open the file to get the number of columns in each line
    with open(filename, "r", encoding=file_encoding) as temp_f:
        # Get the number of columns in each line
        col_count = [len(l.split(",")) for l in temp_f.readlines()]

    # Generate column names (names will be 0, 1, 2, ..., maximum columns - 1)
    column_names = [i for i in range(0, max(col_count))]

    # Read CSV file into a DataFrame
    df = pd.read_csv(filename, header=None,
                     names=column_names, encoding=file_encoding)

    # Find the locations of the keyword "Measurement" in any column. The file onlyhas that when an EIS mesurmment starts
    mask = df.apply(lambda row: row.astype(
        str).str.contains("Measurement"), axis=1)
    mask["Any"] = mask.any(axis=1)
    groups = mask["Any"].cumsum()

    # Split the DataFrame based on the keyword occurrences and drop columns with all NaN values
    split_dfs = {group: df[group == groups].dropna(
        axis=1, how="all") for group in groups.unique()}

    # Display the split DataFrames if verbose=True, default value is False
    if verbose:
        for key, split_df in split_dfs.items():
            print(
                f"DataFrame for splitting keyword = Measurement occurrence {key}:")
            print(split_df)
            print("\n")

    return split_dfs


def find_row(df, keyword):
    """This function finds the index of a row containiing a keyword
    Args:
    - df : DataFrame where we are searching
    - keyword (str): the keyword it searches"""

    return df[df.apply(lambda row: row.astype(str).str.contains(keyword)).any(axis=1)].index[0]


def format_impedance_data(split_dfs):
    """
    Formats the data extracted from split_dfs, filtering the data related to Impedance measurements.

    Args:
    - split_dfs (dict): A dictionary containing values as dataframes for different measurements,
    that are the result of the function getdata(filename)

    Returns:
    - impedance_dfs (dict): A dictionary storing dataframes related to Impedance measurements,
      indexed by their respective keys, each containing the measurement name, date, and the actual data.
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
            name_row = find_row(df, "Measurement")
            new_name = df.iloc[name_row][1]

            # Find the row index that contains 'Date and time' for the date and time
            date_row = find_row(df, "Date and time")
            date_time = df.iloc[date_row][1]

            # Find the index of the row containing the string 'freq / Hz' to use as df header
            freq_row = find_row(df, "freq / Hz")
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
    if dfs_with_freq:
        n = len(dfs_with_freq)
        print(f"There are {n} Impedance measurements")
    else:
        print("The are no Impedance measurements")

    return impedance_dfs


def format_DC_data(split_dfs):
    """
    Extracts and formats DC (direct current) measurement data from a collection of DataFrames.

    Args:
    split_dfs (dict): A dictionary containing DataFrames to process,
    comes from the funtion getdata(filename)

    Returns:
    dict: Dictionary of formatted DC measurement data.
    """

    dfs_DC_meas = []
    DC_data = False
    # Process each DataFrame in the input dictionary
    for key, df in split_dfs.items():
        # Check for the presence of 'Date and time measurement:', only present in dataframes of DC measurements
        if (
            df.apply(lambda row: row.astype(str).str.contains(
                "Date and time measurement:"))
            .any()
            .any()
        ):
            DC_data = True
            # Reset the index of the dataframe
            df = split_dfs[key].reset_index(drop=True)

            # Find and remove the row index containing 'File date:' because it belongs to EIS measurements
            # it is an artifact of how the different dataframes were split by getdata(filename)
            row_filedate = find_row(df, "File date:")
            df = df.drop(df.index[row_filedate])

            # Create a dictionary of DataFrames with two columns each
            # (each DC measurements only consists on 2 columns that can change in the magnitude measured
            # possible magnitudes: time(s), Voltage (V), Currrent (microA)
            DC_dfs = {
                f"DC measurement {int(i/2)}": df.iloc[:, i: i + 2]
                for i in range(0, df.shape[1], 2)
            }
    if DC_data:
        # Select the first DataFrame 'DC measurement 0' as example to find rows
        df = DC_dfs["DC measurement 0"]

        # Find the row index for date/time of measurement, name of measurement and units
        date_row = find_row(df, "Date and time measurement:")
        name_row = date_row - 1
        units_row = date_row + 1

        # Process each DataFrame in the generated dictionary
        for key, df in DC_dfs.items():
            dfs_DC_meas.append(key)
            # Extract date and time information
            date_time = df.iloc[date_row, 1]
            new_name = df.iloc[name_row, 0].split(":")[0]

            # Set column headers as the units row
            df.columns = df.iloc[units_row]
            df = df.drop(units_row).drop(index=range(0, units_row))
            df.dropna(how="all", inplace=True)

            # Store the extracted information and data in the 'DC_dfs' dictionary
            DC_dfs[key] = {"Name": new_name,
                           "Date and Time": date_time, "Data": df}
            new_key = f"DC measurement ({key})"

        n = len(dfs_DC_meas)
        print(f"There are {n} direct current measurements")
        return DC_dfs
    else:
        print("There are no direct current measurements")
