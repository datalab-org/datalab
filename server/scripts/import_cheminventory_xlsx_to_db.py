import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue
data_collection = db.data

def main(xlsx_filename): 
   df=  pd.read_excel(xlsx_filename, engine="openpyxl")

   # filter out starting materials without barcodes
   df = df[df.Barcode != " "] 
   df = df[~df.Barcode.isna()]

   df["item_id"] = df["Barcode"]

   df["item_kind"] = "starting material"
   df["status"] = "exists"

   print(f"adding {len(df)} entries into data collection")
   print(df.head())
   proceed = input("Continue? (y/n)\n")
   if proceed=="y":
      data_collection.insert_many(df.to_dict('records'))
   else:
      print("insert cancelled")

if __name__ == "__main__":
   import plac; plac.call(main)