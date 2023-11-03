# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 15:09:01 2023

@author: gh513
"""


import pandas as pd
import os.path, glob
import csv
import re
from io import StringIO
import numpy as np

<<<<<<< HEAD
# The following lines adjust the granularity of reporting. 
#pd.options.display.max_rows = 10
#pd.options.display.max_columns = 10
#pd.options.display.float_format = "{:.1f}".format
<<<<<<< HEAD


<<<<<<< HEAD
<<<<<<< HEAD
filename = "PalmSense_test_datalab_shorter.csv"
file_encoding = 'utf-16 LE'
=======


filename = "PalmSense_test_datalab_shorter.csv"
file_encoding = 'utf-16 LE'

def getdata():
    """Loads all the experimental data to a dataframe per excel sheet"""
            # set file_encoding to the file encoding (utf8, latin1, etc.)
    #df = pd.read_csv(file, header = 2, encoding = file_encoding, index_col = False, names=range(25))

    with open(filename, 'r', encoding = file_encoding) as temp_f:
        # get No of columns in each line
        col_count = [ len(l.split(",")) for l in temp_f.readlines() ]
>>>>>>> cc22c82 (Palmsense reader code now can load the data and separate in different df according to keyword Impedance)


def getdata(filename, file_encoding='utf-16 LE', verbose = False):
=======
filename = "PalmSense_test_datalab_shorter.csv" # file with experimetnal data as exported "as csv" from PSTrace
=======
filename = "PalmSense_test_datalab.csv" # file with experimetnal data as exported "as csv" from PSTrace
>>>>>>> 4fa42bc (code reads all parts of csv output file from PSTrace)
=======

<<<<<<< HEAD
filename = "PalmSense_test_datalab_EIS.csv" # file with experimetnal data as exported "as csv" from PSTrace
>>>>>>> 3378ab0 (solved issues with cases where there are no DC current experiments)
=======
filename = "PalmSense_test_datalab.csv" # file with experimetnal data as exported "as csv" from PSTrace
>>>>>>> 611b9a2 (solved bug)
keyword = "Measurement" #keyword to split input file on


def getdata(filename, file_encoding='utf-16 LE', verbose = False ):
>>>>>>> 2d1266c (Formated EIS part of the output files)
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
    with open(filename, 'r', encoding=file_encoding) as temp_f:
        # Get the number of columns in each line
        col_count = [len(l.split(",")) for l in temp_f.readlines()]

    # Generate column names (names will be 0, 1, 2, ..., maximum columns - 1)
    column_names = [i for i in range(0, max(col_count))]

<<<<<<< HEAD
    # Read CSV file into a DataFrame
    df = pd.read_csv(filename, header=None, names=column_names, encoding=file_encoding)

    # Find the locations of the keyword in any column
    mask = df.apply(lambda row: row.astype(str).str.contains(keyword), axis=1)
    mask['Any'] = mask.any(axis=1)
    groups = mask["Any"].cumsum()

    # Split the DataFrame based on the keyword occurrences and drop columns with all NaN values
    split_dfs = {group: df[group == groups].dropna(axis=1, how='all') 
                                         for group in groups.unique()}
    
    # Display the split DataFrames if verbose=True, default value is False
    if verbose: 
        for key, split_df in split_dfs.items():
            print(f"DataFrame for '{keyword}' occurrence {key}:")
            print(split_df)
            print("\n")

    return split_dfs


<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD




=======
    ### Read csv
    df = pd.read_csv(filename, header=None, names=column_names,encoding = file_encoding)

#    print(dfhead)
  #  print (df.head(n=10))

    df.to_csv("test.csv")

    
    # Keyword to split on
    keyword = 'Impedance'
    
    # Find the locations of the keyword in any column
    mask = df.apply(lambda row: row.astype(str).str.contains(keyword), axis=1)
    mask['Any'] = mask.any(axis=1)
    groups = mask["Any"].cumsum()

    # Splitting the DataFrame based on the keyword occurrences
    split_dfs = {group: df[group == groups] for group in groups.unique()}
    
    # Display the split DataFrames
    for key, split_df in split_dfs.items():
        print(f"DataFrame for '{keyword}' occurrence {key}:")
        print(split_df)
        print("\n")





    
    return df
>>>>>>> cc22c82 (Palmsense reader code now can load the data and separate in different df according to keyword Impedance)
=======
def formatdata(split_dfs):
=======
# def formatdata(split_dfs):
>>>>>>> c84820a (Cleaned and documented code for impedance spectroscopy data formating)
    
#     dfs_with_freq= []
#     impedance_dfs = {}
#     for key, df in split_dfs.items():
        
#         if df.apply(lambda row: row.astype(str).str.contains('freq / Hz')).any().any():
#             dfs_with_freq.append(key)
#             df = split_dfs[key].reset_index(drop=True)
#             name_row = (df[df.apply(lambda row: row.astype(str).str.contains('Measurement'))
#                                 .any(axis=1)].index[0])
#             new_name = df.iloc[name_row][1]
#             date_row = (df[df.apply(lambda row: row.astype(str).str.contains('Date and time'))
#                                 .any(axis=1)].index[0])
#             date_time =  df.iloc[date_row][1]
#             print(date_time)
            
            
        

#             # Find the index of the row containing the string 'freq / Hz'
#             index_with_freq = (df[df.apply(lambda row: row.astype(str).str.contains('freq / Hz'))
#                                 .any(axis=1)].index[0])
     
#             # Set the row with 'freq / Hz' as the header
#             df.columns = df.iloc[index_with_freq]
     
#             # Remove the row that contains 'freq / Hz' and rows before it (index < index_with_freq)
#             df = df.drop(index_with_freq).drop(index=range(0, index_with_freq))
     
#             # Display the DataFrame after setting the header and removing unnecessary rows
#             impedance_dfs[new_name]= {"Date and Time" : date_time, "Data": df}
             
#     if dfs_with_freq:
#         n = len (dfs_with_freq)
#         print(impedance_dfs)
#         print(f"There are {n} Impedance measurements")
    
#     else:
#         print("No part of this file contains Impedance measurements")


=======
>>>>>>> 4fa42bc (code reads all parts of csv output file from PSTrace)

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
        
        if df.apply(lambda row: row.astype(str).str.contains('freq / Hz')).any().any():
            # Reset the index of the dataframe
            df = split_dfs[key].reset_index(drop=True)            
            dfs_with_freq.append(key)
            
            # Find the row index that contains 'Measurement' to find the name to use
            name_row = df[df.apply(lambda row: row.astype(str).str.contains('Measurement'))
                           .any(axis=1)].index[0]
            new_name = df.iloc[name_row][1]
            
            # Find the row index that contains 'Date and time' for the date and time
            date_row = df[df.apply(lambda row: row.astype(str).str.contains('Date and time'))
                           .any(axis=1)].index[0]
            date_time = df.iloc[date_row][1]
            
            # Find the index of the row containing the string 'freq / Hz' to use as df header
            index_with_freq = df[df.apply(lambda row: row.astype(str).str.contains('freq / Hz'))
                                 .any(axis=1)].index[0]
            df.columns = df.iloc[index_with_freq]
     
            # Remove the row that contains 'freq / Hz' and rows before it
            df = df.drop(index_with_freq).drop(index=range(0, index_with_freq))
            
            # Store the extracted information and data in the impedance_dfs dictionary
            impedance_dfs[f"EIS measurement {key}"] = {"Name" : new_name, "Date and Time": date_time, "Data": df}
           # new_key = f"EIS ({key})"
           # impedance_dfs[new_key] = impedance_dfs.pop(key)
            
            
    # Check if there are dataframes with 'freq / Hz'
    if dfs_with_freq:
        n = len(dfs_with_freq)
        print(f"There are {n} Impedance measurements")
    else:
        print("The are no Impedance measurements")
                
<<<<<<< HEAD
>>>>>>> 2d1266c (Formated EIS part of the output files)

=======
    return impedance_dfs
<<<<<<< HEAD
        
        
>>>>>>> c84820a (Cleaned and documented code for impedance spectroscopy data formating)
=======


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
        if df.apply(lambda row: row.astype(str).str.contains('Date and time measurement:')).any().any():
            DC_data = True
            # Reset the index of the dataframe
            df = split_dfs[key].reset_index(drop=True)
            

            # Find and remove the row index containing 'File date:' because it belongs to EIS measurements
            # it is an artifact of how the different dataframes were split by getdata(filename)
            row_filedate = df[df.apply(lambda row: row.astype(str).str.contains('File date:'))
                              .any(axis=1)].index[0]
            df = df.drop(df.index[row_filedate])

            # Create a dictionary of DataFrames with two columns each 
            # (each DC measurements only consists on 2 columns that can change in the magnitude measured
            # possible magnitudes: time(s), Voltage (V), Currrent (microA)
            DC_dfs = {f"DC measurement {int(i/2)}": df.iloc[:, i:i+2] for i in range(0, df.shape[1], 2)}
    if DC_data:
        # Select the first DataFrame 'DC measurement 0' as example to find rows
        df = DC_dfs["DC measurement 0"]

        # Find the row index for date/time of measurement, name of measurement and units 
        date_row = df[df.apply(lambda row: row.astype(str).str.contains('Date and time measurement:'))
                      .any(axis=1)].index[0]
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
            df.dropna(how='all', inplace=True)
            # Store the extracted information and data in the 'DC_dfs' dictionary
            DC_dfs[key] = {"Name": new_name, "Date and Time": date_time, "Data": df}
            new_key = f"DC measurement ({key})"

        n = len(dfs_DC_meas)
        print(f"There are {n} direct current measurements")
        return DC_dfs
    else:
        print("There are no direct current measurements")

    


                  
>>>>>>> 4fa42bc (code reads all parts of csv output file from PSTrace)
def main():
    """ Main program """

    split_dfs = getdata(filename, verbose = False )
    
    eis_data = format_impedance_data(split_dfs)

    DC_data = format_DC_data(split_dfs)
    
    print(eis_data)    
    print (DC_data)

            
if __name__ == "__main__":
    
    
    

    #Call main program
    main()