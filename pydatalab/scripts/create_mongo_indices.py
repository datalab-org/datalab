from pymongo import TEXT, MongoClient

from pydatalab.config import CONFIG
from pydatalab.models import ITEM_MODELS

client: MongoClient = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

fts_fields = set()
for model in ITEM_MODELS:
    schema = ITEM_MODELS[model].schema()
    for f in schema["properties"]:
        if schema["properties"][f]["type"] == "string":
            fts_fields.add(f)

response = db.items.create_index([(k, TEXT) for k in fts_fields], name="items_fts")
response = db.items.create_index("type")
response = db.items.create_index("item_id", unique=True)
