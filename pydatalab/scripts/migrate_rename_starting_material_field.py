from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

# because spelling is hard
db.items.update_many(
    {"date_aquired": {"$exists": True}}, {"$rename": {"date_aquired": "date_acquired"}}
)
