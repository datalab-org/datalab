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

# The following lines adjust the granularity of reporting. 
#pd.options.display.max_rows = 10
#pd.options.display.max_columns = 10
#pd.options.display.float_format = "{:.1f}".format


filename = "PalmSense_test_datalab_shorter.csv"
file_encoding = 'utf-16 LE'


def getdata(filename, file_encoding='utf-16 LE', verbose = False):
    """
    Loads experimental data from a CSV file, splits the DataFrame based on a specified keyword,
    and returns a dictionary containing the resulting DataFrames.

    Args:
    - filename (str): Name of the CSV file
    - file_encoding (str): Encoding type for the CSV file, default is 'utf-16 LE'

    Returns:
    - split_dfs (dict): Dictionary containing DataFrames split based on the keyword
    """


    # Open the file to get the number of columns in each line
    with open(filename, 'r', encoding=file_encoding) as temp_f:
        # Get the number of columns in each line
        col_count = [len(l.split(",")) for l in temp_f.readlines()]

    # Generate column names (names will be 0, 1, 2, ..., maximum columns - 1)
    column_names = [i for i in range(0, max(col_count))]

    # Read CSV file into a DataFrame
    df = pd.read_csv(filename, header=None, names=column_names, encoding=file_encoding)

    # Keyword to split on
    keyword = 'Measurement'

    # Find the locations of the keyword in any column
    mask = df.apply(lambda row: row.astype(str).str.contains(keyword), axis=1)
    mask['Any'] = mask.any(axis=1)
    groups = mask["Any"].cumsum()

    # Split the DataFrame based on the keyword occurrences and drop columns with all NaN values
    split_dfs = {group: df[group == groups].dropna(axis=1, how='all') 
                                         for group in groups.unique()}
    
    # Display the split DataFrames
    if verbose == True: 
        for key, split_df in split_dfs.items():
            print(f"DataFrame for '{keyword}' occurrence {key}:")
            print(split_df)
            print("\n")

    return split_dfs







def main():
    """ Main program """


    """ Get the experimental data"""
  #  df = getdata2()

    split_dfs = getdata(filename, verbose = False )
    print(split_dfs)
    
    """ We plot experimental CV"""  
    #plot(df)

    #This is because Anaconda writes a lot of temporary files in my computer, not needed in datalab
    for file in glob.glob("tmp*"):
        os.remove(file)
        
            
if __name__ == "__main__":
    
    
    

    #Call main program
    main()