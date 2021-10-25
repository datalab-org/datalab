from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

data_collection = db.data

data_collection.update_many({}, {"$rename": {"item_kind": "type"}})


data_collection.update_many({"type": "sample"}, {"$set": {"type": "samples"}})
