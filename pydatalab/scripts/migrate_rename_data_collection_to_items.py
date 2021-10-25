from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

db.data.copyTo("items")
