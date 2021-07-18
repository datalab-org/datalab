import pandas as pd
from pymongo import MongoClient
import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue
data_collection = db.data


def main(xlsx_filename): 
   df=  pd.read_excel(xlsx_filename, engine="openpyxl")
   df["item_kind"] = "starting material"

   # filter out starting materials without barcodes
   df = df[df["Barcode"] != " "] 
   df = df[~df.Barcode.isna()]

   df["item_id"] = df["Barcode"]
   df["item_kind"] = "starting material"
   df["last_modified"] = datetime.datetime.now().isoformat()
   
   # get ids of all starting materials that were already in the database
   cursor = data_collection.aggregate(
      [{
         "$match": {"item_kind": "starting material"}
      },
      {
         "$project": {
            "_id":0,
            "item_id":1,
            }
      }])
   existing_starting_material_ids = pd.Series([d["item_id"] for d in cursor])

   # find ids that have been deleted since the last update
   deleted_ids = existing_starting_material_ids[~existing_starting_material_ids.isin(df["item_id"])]
   print(f"found {len(deleted_ids)} deleted entries since last update. Will mark them as deleted in the db:")
   if len(deleted_ids):
      print(deleted_ids)
   else: print("none")

   for deleted_id in deleted_ids:
      data_collection.update_one( {"item_id": deleted_id},
         {"$set": {"status": "deleted"}}
         )

   print(f"updating or adding {len(df)} entries into data collection")
   print(df.head())

   records = df.to_dict('records')
   for record in records:
      data_collection.update_one(
         {  "item_id": record["item_id"]},
         {   "$set": record },
         upsert=True
      )


if __name__ == "__main__":
   import plac; plac.call(main)