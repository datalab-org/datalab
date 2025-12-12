from flask import Blueprint, jsonify, request

from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only, get_default_permissions

GRAPHS = Blueprint("graphs", __name__)


@GRAPHS.before_request
@active_users_or_get_only
def _(): ...


@GRAPHS.route("/item-graph", methods=["GET"])
@GRAPHS.route("/item-graph/<item_id>", methods=["GET"])
def get_graph_cy_format(
    item_id: str | None = None,
    collection_id: str | None = None,
    hide_collections: bool = True,
    max_depth: int = 1,
):
    collection_id = request.args.get("collection_id", type=str)
    hide_collections = request.args.get(
        "hide_collections", default=True, type=lambda v: v.lower() == "true"
    )
    max_depth = request.args.get("max_depth", default=1, type=int)

    if item_id is None:
        if collection_id is not None:
            collection_immutable_id = flask_mongo.db.collections.find_one(
                {"collection_id": collection_id, **get_default_permissions(user_only=False)},
                projection={"_id": 1},
            )
            if not collection_immutable_id:
                return (
                    jsonify(
                        status="error", message=f"No collection found with ID {collection_id!r}"
                    ),
                    404,
                )
            collection_immutable_id = collection_immutable_id["_id"]
            query = {
                "$and": [
                    {"relationships.immutable_id": collection_immutable_id},
                    {"relationships.type": "collections"},
                ]
            }
        else:
            query = {}
        all_documents = flask_mongo.db.items.find(
            {**query, **get_default_permissions(user_only=False)},
            projection={"item_id": 1, "name": 1, "type": 1, "relationships": 1},
        )
        node_ids: set[str] = {document["item_id"] for document in all_documents}
        all_documents.rewind()

    else:
        main_item = flask_mongo.db.items.find_one(
            {
                "item_id": item_id,
                **get_default_permissions(user_only=False),
            },
            projection={"item_id": 1, "name": 1, "type": 1, "relationships": 1},
        )

        if not main_item:
            return (
                jsonify(status="error", message=f"Item {item_id} not found or no permission"),
                404,
            )

        node_ids = {item_id}
        all_documents = [main_item]

        def add_related_items(current_item_id: str, current_depth: int):
            if current_depth > max_depth:
                return

            current_item = flask_mongo.db.items.find_one(
                {
                    "item_id": current_item_id,
                    **get_default_permissions(user_only=False),
                },
                projection={"item_id": 1, "name": 1, "type": 1, "relationships": 1},
            )

            if not current_item:
                return

            for relationship in current_item.get("relationships", []) or []:
                if relationship.get("item_id") and relationship["item_id"] not in node_ids:
                    node_ids.add(relationship["item_id"])
                    related_item = flask_mongo.db.items.find_one(
                        {
                            "item_id": relationship["item_id"],
                            **get_default_permissions(user_only=False),
                        },
                        projection={"item_id": 1, "name": 1, "type": 1, "relationships": 1},
                    )
                    if related_item:
                        all_documents.append(related_item)
                        add_related_items(relationship["item_id"], current_depth + 1)

            incoming_items = list(
                flask_mongo.db.items.find(
                    {
                        "relationships": {
                            "$elemMatch": {
                                "item_id": current_item_id,
                            }
                        },
                        **get_default_permissions(user_only=False),
                    },
                    projection={"item_id": 1, "name": 1, "type": 1, "relationships": 1},
                )
            )

            for incoming_item in incoming_items:
                if incoming_item["item_id"] not in node_ids:
                    node_ids.add(incoming_item["item_id"])
                    all_documents.append(incoming_item)
                    add_related_items(incoming_item["item_id"], current_depth + 1)

        add_related_items(item_id, 1)

    nodes = []
    edges = []

    # Collect the elements that have already been added to the graph, to avoid duplication
    drawn_elements = set()
    node_collections: set[str] = set()
    for document in all_documents:
        # for some reason, document["relationships"] is sometimes equal to None, so we
        # need this `or` statement.
        for relationship in document.get("relationships") or []:
            # only considering child-parent relationships
            if relationship.get("type") == "collections" and not collection_id:
                if hide_collections:
                    continue
                collection_data = flask_mongo.db.collections.find_one(
                    {
                        "_id": relationship["immutable_id"],
                        **get_default_permissions(user_only=False),
                    },
                    projection={"collection_id": 1, "title": 1, "type": 1},
                )
                if collection_data:
                    if relationship["immutable_id"] not in node_collections:
                        _id = f"Collection: {collection_data['collection_id']}"
                        if _id not in drawn_elements:
                            nodes.append(
                                {
                                    "data": {
                                        "id": _id,
                                        "name": collection_data["title"],
                                        "type": collection_data["type"],
                                        "shape": "triangle",
                                    }
                                }
                            )
                            node_collections.add(relationship["immutable_id"])
                            drawn_elements.add(_id)

                    source = f"Collection: {collection_data['collection_id']}"
                    target = document.get("item_id")
                    if target in node_ids:
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
                continue

        for relationship in document.get("relationships") or []:
            # only considering child-parent relationships:
            if relationship.get("relation") not in ("parent", "is_part_of"):
                continue

            target = document["item_id"]
            source = relationship["item_id"]
            if source not in node_ids or target not in node_ids:
                continue
            edge_id = f"{source}->{target}"
            if edge_id not in drawn_elements:
                drawn_elements.add(edge_id)
                edges.append(
                    {
                        "data": {
                            "id": edge_id,
                            "source": source,
                            "target": target,
                            "value": 1,
                        }
                    }
                )

        if document["item_id"] not in drawn_elements:
            drawn_elements.add(document["item_id"])
            nodes.append(
                {
                    "data": {
                        "id": document["item_id"],
                        "name": document["name"] if document["name"] else document["item_id"],
                        "type": document["type"],
                        "special": document["item_id"] == item_id,
                    }
                }
            )

    whitelist = {edge["data"]["source"] for edge in edges} | {
        edge["data"]["target"] for edge in edges
    }
    if item_id:
        whitelist.add(item_id)

    nodes = [
        node
        for node in nodes
        if node["data"]["type"] in ("samples", "cells")
        or node["data"]["id"] in whitelist
        or node["data"]["id"].startswith("Collection:")
    ]

    return (jsonify(status="success", nodes=nodes, edges=edges), 200)
