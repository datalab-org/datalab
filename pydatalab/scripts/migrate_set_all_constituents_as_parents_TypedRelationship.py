from pymongo import MongoClient

from pydatalab.config import CONFIG
from pydatalab.models.relationships import RelationshipType, TypedRelationship

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue


all_documents = db.items.find()

for document in all_documents:
    if "synthesis_constituents" not in document:
        continue
    constituent_items = [entry["item"] for entry in document["synthesis_constituents"]]

    print(
        f"Item {document['item_id']} has constituents: {constituent_items}. Creating relationships from these."
    )

    relationships = [
        TypedRelationship(
            description="Is a constituent of",
            relation=RelationshipType.PARENT,
            type=item["type"],
            item_id=item["item_id"],
        ).dict()
        for item in constituent_items
    ]

    db.items.update_one(
        {"item_id": document["item_id"]},
        {"$addToSet": {"relationships": {"$each": relationships}}},
        upsert=True,
    )

    # # # add all constituents as parents to this item (addToSet only adds if its not already there)
    # for constituent_id, item_type in zip(constituent_ids, types):
    #     print(constituent_id, item_type)
    #     relationship = TypedRelationship(
    #         description = "Is a constituent of",
    #         relation = RelationshipType.PARENT,
    #         type = item_type,
    #         item_id = constituent_id,
    #         )
    # db.items.update_one(
    #     {"item_id": document["item_id"]},
    #     {"$addToSet": {"parent_items": {"$each": constituent_ids}}},
    # )

    # # add this item as children in each constituent
    # for constituent_id in constituent_ids:
    #     db.items.update_one(
    #         {"item_id": constituent_id}, {"$addToSet": {"child_items": document["item_id"]}}
    #     )
