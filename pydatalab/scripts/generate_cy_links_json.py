import json

from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

all_documents = db.items.find()

nodes = []
edges = []
for document in all_documents:
    if ("parent_items" not in document) and ("child_items" not in document):
        continue
    nodes.append(
        {"data": {"id": document["item_id"], "name": document["name"], "type": document["type"]}}
    )
    if "parent_items" not in document:
        continue
    for parent_id in document["parent_items"]:
        target = document["item_id"]
        source = parent_id
        edges.append(
            {
                "data": {
                    "id": f"{source}->{target}",
                    "source": source,
                    "target": target,
                    "value": 1,
                }
            }
        )


with open("cy_links_production.json", "w") as f:
    json.dump({"nodes": nodes, "edges": edges}, f)
