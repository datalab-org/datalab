import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue
data_collection = db.data

print(f"starting number of entries in data collection: {data_collection.estimated_document_count()}")


data_collection.delete_many({
      "item_kind": "starting material"
   })

print(f"ending number of entries in data collection: {data_collection.estimated_document_count()}")