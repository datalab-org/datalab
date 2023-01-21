from typing import Callable, Dict

from flask import jsonify

from pydatalab.mongo import flask_mongo


def get_graph_cy_format():

    all_documents = flask_mongo.db.items.find()

    nodes = []
    edges = []
    for document in all_documents:

        nodes.append(
            {
                "data": {
                    "id": document["item_id"],
                    "name": document["name"],
                    "type": document["type"],
                }
            }
        )

        if not document.get("relationships"):
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

    return (jsonify(status="success", nodes=nodes, edges=edges), 200)


get_graph_cy_format.methods = ("GET",)  # type: ignore


ENDPOINTS: Dict[str, Callable] = {
    "/item-graph/": get_graph_cy_format,
}
