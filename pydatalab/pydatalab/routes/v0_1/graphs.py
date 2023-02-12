from typing import Callable, Dict

from flask import jsonify

from pydatalab.mongo import flask_mongo
from pydatalab.routes.utils import get_default_permissions


def get_graph_cy_format():

    all_documents = flask_mongo.db.items.find(
        {
            "$and": [
                {
                    "$or": [
                        {"type": "samples"},
                        {
                            "$and": [
                                {"type": "starting_materials"},
                                {"relationships.0": {"$exists": True}},
                            ]
                        },
                    ]
                },
                {**get_default_permissions(user_only=False)},
            ]
        },
        projection={"item_id": 1, "name": 1, "type": 1, "relationships": 1},
    )

    nodes = []
    edges = []
    for document in all_documents:

        node_collections = set()
        for relationship in document.get("relationships", []):
            # only considering child-parent relationships:
            if relationship.get("type") == "collections":
                node_collections.add(relationship["immutable_id"])
                continue

            if relationship.get("relation") != "parent":
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

        nodes.append(
            {
                "data": {
                    "id": document["item_id"],
                    "name": document["name"],
                    "type": document["type"],
                    "collections": list(node_collections),
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

    return (jsonify(status="success", nodes=nodes, edges=edges), 200)


get_graph_cy_format.methods = ("GET",)  # type: ignore


ENDPOINTS: Dict[str, Callable] = {
    "/item-graph/": get_graph_cy_format,
}
