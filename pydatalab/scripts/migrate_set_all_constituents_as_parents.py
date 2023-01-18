from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue


all_documents = db.items.find()

for document in all_documents:
    if "synthesis_constituents" not in document:
        continue
    constituent_ids = [entry["item"]["item_id"] for entry in document["synthesis_constituents"]]

    print(
        f"Item {document['item_id']} has constituents: {constituent_ids}. Creating relationships from these."
    )

    # add all constituents as parents to this item (addToSet only adds if its not already there)
    db.items.update_one(
        {"item_id": document["item_id"]},
        {"$addToSet": {"parent_items": {"$each": constituent_ids}}},
    )

    # add this item as children in each constituent
    for constituent_id in constituent_ids:
        db.items.update_one(
            {"item_id": constituent_id}, {"$addToSet": {"child_items": document["item_id"]}}
        )
