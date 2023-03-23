from pydatalab.mongo import get_database

db = get_database()

for item in db.items.find({"blocks_obj": {"$ne": {}}}):
    print(f"processing item {item['item_id']}")
    for key in item["blocks_obj"]:
        if item["blocks_obj"][key]["blocktype"] == "image":
            print(f"need to update block: {key}")
            db.items.update_one(
                {"item_id": item["item_id"]}, {"$set": {f"blocks_obj.{key}.blocktype": "media"}}
            )
