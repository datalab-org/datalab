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
    
    dfs_with_freq= []
    impedance_dfs = {}
    for key, df in split_dfs.items():
        
        if df.apply(lambda row: row.astype(str).str.contains('freq / Hz')).any().any():
            dfs_with_freq.append(key)
            df = split_dfs[key].reset_index(drop=True)
            name_row = (df[df.apply(lambda row: row.astype(str).str.contains('Measurement'))
                                .any(axis=1)].index[0])
            new_name = df.iloc[name_row][1]
            date_row = (df[df.apply(lambda row: row.astype(str).str.contains('Date and time'))
                                .any(axis=1)].index[0])
            date_time =  df.iloc[date_row][1]
            print(date_time)
            #reset the index for compatibility when finding it
            
        

            # Find the index of the row containing the string 'freq / Hz'
            index_with_freq = (df[df.apply(lambda row: row.astype(str).str.contains('freq / Hz'))
                                .any(axis=1)].index[0])
     
            # Set the row with 'freq / Hz' as the header
            df.columns = df.iloc[index_with_freq]
     
            # Remove the row that contains 'freq / Hz' and rows before it (index < index_with_freq)
            df = df.drop(index_with_freq).drop(index=range(0, index_with_freq))
     
            # Display the DataFrame after setting the header and removing unnecessary rows
            impedance_dfs[new_name]= {"Date and Time" : date_time,"Data": df}
             
    if dfs_with_freq:
        n = len (dfs_with_freq)
        print(impedance_dfs)
        print(f"There are {n} Impedance measurements")
    
    else:
        print("No part of this file contains Impedance measurements")
                
>>>>>>> 2d1266c (Formated EIS part of the output files)

def main():
    """ Main program """


    """ Get the experimental data"""
  #  df = getdata2()

    split_dfs = getdata(filename, verbose = False )

    for key, df in split_dfs.items():
        df.to_csv(f"{key}.csv")
    
    formatdata(split_dfs)



    
    """ We plot experimental CV"""  
    #plot(df)

    #This is because Anaconda writes a lot of temporary files in my computer, not needed in datalab
    for file in glob.glob("tmp*"):
        os.remove(file)
        
            
if __name__ == "__main__":
    
    
    

    #Call main program
    main()