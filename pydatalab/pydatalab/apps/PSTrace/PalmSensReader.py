# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 15:09:01 2023

@author: gh513
"""



import pandas as pd

filename = (
    "PalmSense_test_datalab.csv"  # file with experimetnal data as exported "as csv" from PSTrace
)


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
    df = pd.read_csv(filename, header=None, names=column_names, encoding=file_encoding)

    # Find the locations of the keyword "Measurement" in any column. The file onlyhas that when an EIS mesurmment starts
    mask = df.apply(lambda row: row.astype(str).str.contains("Measurement"), axis=1)
    mask["Any"] = mask.any(axis=1)
    groups = mask["Any"].cumsum()

    # Split the DataFrame based on the keyword occurrences and drop columns with all NaN values
    split_dfs = {group: df[group == groups].dropna(axis=1, how="all") for group in groups.unique()}

    # Display the split DataFrames if verbose=True, default value is False
    if verbose:
        for key, split_df in split_dfs.items():
            print(f"DataFrame for splitting keyword = Measurement occurrence {key}:")
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
            df.apply(lambda row: row.astype(str).str.contains("Date and time measurement:"))
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
                f"DC measurement {int(i/2)}": df.iloc[:, i : i + 2]
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
            DC_dfs[key] = {"Name": new_name, "Date and Time": date_time, "Data": df}
            new_key = f"DC measurement ({key})"

        n = len(dfs_DC_meas)
        print(f"There are {n} direct current measurements")
        return DC_dfs
    else:
        print("There are no direct current measurements")


def main():
    """Main program"""

    split_dfs = getdata(filename, verbose=False)

    eis_data = format_impedance_data(split_dfs)

    DC_data = format_DC_data(split_dfs)

    print(eis_data)
    print(DC_data)


if __name__ == "__main__":
    # Call main program
    main()
