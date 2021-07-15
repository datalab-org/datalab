import datetime
import shutil

from pymongo import MongoClient


client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue
file_collection = db.files


all_files = file_collection.find({})


for file in all_files:
    file_collection.update_one(
        {"_id": file["_id"]},
        {
            "$set": {
                "time_added": file["last_modified"],
                "version": 1,
            }
        },
    )
