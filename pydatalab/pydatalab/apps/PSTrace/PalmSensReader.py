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

def getdata():
    """Loads all the experimental data to a dataframe per excel sheet"""
            # set file_encoding to the file encoding (utf8, latin1, etc.)
    #df = pd.read_csv(file, header = 2, encoding = file_encoding, index_col = False, names=range(25))

    with open(filename, 'r', encoding = file_encoding) as temp_f:
        # get No of columns in each line
        col_count = [ len(l.split(",")) for l in temp_f.readlines() ]

    ### Generate column names  (names will be 0, 1, 2, ..., maximum columns - 1)
    column_names = [i for i in range(0, max(col_count))]

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

def main():
    """ Main program """


    """ Get the experimental data"""
    df = getdata()


    """ We plot experimental CV"""  
    #plot(df)

    #This is because Anaconda writes a lot of temporary files in my computer, not needed in datalab
    for file in glob.glob("tmp*"):
        os.remove(file)
        
            
if __name__ == "__main__":
    
    
    

    #Call main program
    main()