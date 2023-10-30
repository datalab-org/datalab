# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 15:09:01 2023

@author: gh513
"""


import pandas as pd
import os.path, glob
import csv

file = "PalmSense_test_datalab.csv"

print (file)
def getdata():
    """Loads all the experimental data to a dataframe per excel sheet"""
    file_encoding = 'utf-16 LE'        # set file_encoding to the file encoding (utf8, latin1, etc.)
    #df = pd.read_csv(file, header = 2, encoding = file_encoding, index_col = False, names=range(25))

    with open(file, 'r', encoding = file_encoding) as temp_f:
        # get No of columns in each line
        col_count = [ len(l.split(",")) for l in temp_f.readlines() ]

    ### Generate column names  (names will be 0, 1, 2, ..., maximum columns - 1)
    column_names = [i for i in range(0, max(col_count))]

    ### Read csv
    df = pd.read_csv(file, header=None, names=column_names,encoding = file_encoding)

#    print(dfhead)
    print (df)

    df.to_csv("test.csv")
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