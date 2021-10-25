from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

db.files.update_many({}, {"$rename": {"last_modified_remote_timestamp": "last_modified_remote"}})
