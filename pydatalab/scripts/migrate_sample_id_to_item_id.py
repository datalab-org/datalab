from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

db.items.update_many({"type": "samples"}, [{"$set": {"item_id": "$sample_id"}}])
