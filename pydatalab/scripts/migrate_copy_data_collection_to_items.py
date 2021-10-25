from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

pipeline = [
    {"$match": {}},
    {"$out": "items"},
]

db.data.aggregate(pipeline)
