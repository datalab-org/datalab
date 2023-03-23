from pydatalab.mongo import get_database

db = get_database()

all_items = list(db.items.find())

for item in all_items:
    print(f"processing item {item['item_id']}")
    for key in item["blocks_obj"]:
        if item["blocks_obj"][key]["blocktype"] == "image":
            print(f"need to update block: {key}")
            db.items.update_one(
                {"item_id": item["item_id"]}, {"$set": {f"blocks_obj.{key}.blocktype": "media"}}
            )
