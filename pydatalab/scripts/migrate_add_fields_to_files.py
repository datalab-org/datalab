from pymongo import MongoClient, uri_parser

from pydatalab.config import CONFIG

client = MongoClient(uri_parser.parse_host(CONFIG.MONGO_URI))
database = uri_parser.parse_uri(CONFIG.MONGO_URI).get("database")
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
