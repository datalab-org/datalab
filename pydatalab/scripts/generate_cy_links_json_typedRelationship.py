import json

from pymongo import MongoClient

from pydatalab.config import CONFIG

client = MongoClient(CONFIG.MONGO_URI)

db = client.datalabvue

all_documents = db.items.find()

nodes = []
edges = []
for document in all_documents:
    nodes.append(
        {"data": {"id": document["item_id"], "name": document["name"], "type": document["type"]}}
    )

    if "relationships" not in document:
        continue

    for relationship in document["relationships"]:
        # only considering child-parent relationships:
        if relationship["relation"] != "parent":
            continue

        target = document["item_id"]
        source = relationship["item_id"]
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


# We want to filter out all the starting materials that don't have relationships since there are so many of them:
whitelist = {edge["data"]["source"] for edge in edges}

nodes = [
    node
    for node in nodes
    if ((node["data"]["type"] == "samples") or (node["data"]["id"] in whitelist))
]


with open("cy_links_production_v2.json", "w") as f:
    json.dump({"nodes": nodes, "edges": edges}, f)
