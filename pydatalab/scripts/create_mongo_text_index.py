from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

response = db.items.create_index({"$**": "text"})
