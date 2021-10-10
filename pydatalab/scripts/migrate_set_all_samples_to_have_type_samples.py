from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

db.items.update_many({"sample_id": {"$exists": True}}, {"$set": {"type": "samples"}})
