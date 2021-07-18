import datetime 
import shutil

from pymongo import MongoClient



client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue
data_collection = db.data


all_samples = list(data_collection.find({}))
print(f"adding item_kind='sample' and item_id=<existing sample_id> to {len(all_samples)} entries in the data collection.")
for sample in all_samples: 
   print(sample["sample_id"])
   data_collection.update_one(
      {"_id": sample["_id"]},
      {
         "$set": {
            "item_kind": "sample",
            "item_id": sample["sample_id"],
         }
      }
   )


