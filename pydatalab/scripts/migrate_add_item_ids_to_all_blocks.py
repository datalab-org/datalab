from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

all_items = db.items.find({})

for item in all_items:
    print(f"processing item: {item['_id']}")
    for block_id in item["blocks_obj"]:
        print(f"\tadding item_id field to block with id: {block_id}")
        res = db.items.update_one(
            {"item_id": item["item_id"]},
            {"$set": {f"blocks_obj.{block_id}.item_id": item["item_id"]}},
        )
