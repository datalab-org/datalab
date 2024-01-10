import datetime
import json
from typing import Callable, Dict, List, Optional, Set, Union

from bson import ObjectId
from flask import jsonify, request
from flask_login import current_user
from pydantic import ValidationError
from pymongo.command_cursor import CommandCursor

from pydatalab.blocks import BLOCK_TYPES
from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS
from pydatalab.models.items import Item
from pydatalab.models.relationships import RelationshipType
from pydatalab.models.utils import generate_unique_refcode
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import get_default_permissions


def reserialize_blocks(display_order: List[str], blocks_obj: Dict[str, Dict]) -> Dict[str, Dict]:
    """Create the corresponding Python objects from JSON block data, then
    serialize it again as JSON to populate any missing properties.

    Parameters:
        blocks_obj: A dictionary containing the JSON block data, keyed by block ID.

    Returns:
        A dictionary with the re-serialized block data.

    """
    for block_id in display_order:
        try:
            block_data = blocks_obj[block_id]
        except KeyError:
            LOGGER.warning(f"block_id {block_id} found in display order but not in blocks_obj")
            continue
        blocktype = block_data["blocktype"]
        blocks_obj[block_id] = (
            BLOCK_TYPES.get(blocktype, BLOCK_TYPES["notsupported"]).from_db(block_data).to_web()
        )

    return blocks_obj


# Seems to be obselete now?
def dereference_files(file_ids: List[Union[str, ObjectId]]) -> Dict[str, Dict]:
    """For a list of Object IDs (as strings or otherwise), query the files collection
    and return a dictionary of the data stored under each ID.

    Parameters:
        file_ids: The list of IDs of files to return;

    Returns:
        The dereferenced data as a dictionary with (string) ID keys.

    """
    results = {
        str(f["_id"]): f
        for f in flask_mongo.db.files.find(
            {
                "_id": {"$in": [ObjectId(_id) for _id in file_ids]},
            }
        )
    }
    if len(results) != len(file_ids):
        raise RuntimeError(
            "Some file IDs did not have corresponding database entries.\n"
            f"Returned: {list(results.keys())}\n"
            f"Requested: {file_ids}\n"
        )

    return results


def get_equipment_summary():
    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                status="error",
                message="Authorization required to access chemical inventory.",
            ),
            401,
        )

    _project = {
        "_id": 0,
        "creators": {
            "display_name": 1,
            "contact_email": 1,
        },
        # "collections": {
        #     "collection_id": 1,
        #     "title": 1,
        # },
        "item_id": 1,
        "name": 1,
        "nblocks": {"$size": "$display_order"},
        "characteristic_chemical_formula": 1,
        "type": 1,
        "date": 1,
        "refcode": 1,
        "location": 1,
    }

    items = [
        doc
        for doc in flask_mongo.db.items.aggregate(
            [
                {
                    "$match": {
                        "type": "equipment",
                        **get_default_permissions(user_only=False),
                    }
                },
                {"$project": _project},
            ]
        )
    ]
    return jsonify({"status": "success", "items": items})


get_equipment_summary.methods = ("GET",)  # type: ignore


def get_starting_materials():
    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                status="error",
                message="Authorization required to access chemical inventory.",
            ),
            401,
        )

    items = [
        doc
        for doc in flask_mongo.db.items.aggregate(
            [
                {
                    "$match": {
                        "type": "starting_materials",
                        **get_default_permissions(user_only=False),
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "item_id": 1,
                        "nblocks": {"$size": "$display_order"},
                        "date_acquired": 1,
                        "chemform": 1,
                        "name": 1,
                        "chemical_purity": 1,
                        "supplier": 1,
                        "location": 1,
                    }
                },
            ]
        )
    ]
    return jsonify({"status": "success", "items": items})


get_starting_materials.methods = ("GET",)  # type: ignore


def get_samples_summary(
    match: Optional[Dict] = None, project: Optional[Dict] = None
) -> CommandCursor:
    """Return a summary of item entries that match some criteria.

    Parameters:
        match: A MongoDB aggregation match query to filter the results.
        project: A MongoDB aggregation project query to filter the results, relative
            to the default included below.

    """
    if not match:
        match = {}
    match.update(get_default_permissions(user_only=False))
    match["type"] = {"$in": ["samples", "cells"]}

    _project = {
        "_id": 0,
        "creators": {
            "display_name": 1,
            "contact_email": 1,
        },
        "collections": {
            "collection_id": 1,
            "title": 1,
        },
        "item_id": 1,
        "name": 1,
        "chemform": 1,
        "nblocks": {"$size": "$display_order"},
        "characteristic_chemical_formula": 1,
        "type": 1,
        "date": 1,
        "refcode": 1,
    }

    # Cannot mix 0 and 1 keys in MongoDB project so must loop and check
    if project:
        for key in project:
            if project[key] == 0:
                _project.pop(key, None)
            else:
                _project[key] = 1

    return flask_mongo.db.items.aggregate(
        [
            {"$match": match},
            {"$lookup": creators_lookup()},
            {"$lookup": collections_lookup()},
            {"$project": _project},
            {"$sort": {"date": -1}},
        ]
    )


def creators_lookup() -> Dict:
    return {
        "from": "users",
        "let": {"creator_ids": "$creator_ids"},
        "pipeline": [
            {
                "$match": {
                    "$expr": {
                        "$in": ["$_id", {"$ifNull": ["$$creator_ids", []]}],
                    },
                }
            },
            {"$project": {"_id": 0, "display_name": 1, "contact_email": 1}},
        ],
        "as": "creators",
    }


def files_lookup() -> Dict:
    return {
        "from": "files",
        "localField": "file_ObjectIds",
        "foreignField": "_id",
        "as": "files",
    }


def collections_lookup() -> Dict:
    """Looks inside the relationships of the item, searches for IDs in the collections
    table and then projects only the collection ID and name for the response.

    """

    return {
        "from": "collections",
        "let": {"collection_ids": "$relationships.immutable_id"},
        "pipeline": [
            {
                "$match": {
                    "$expr": {
                        "$in": ["$_id", {"$ifNull": ["$$collection_ids", []]}],
                    },
                    "type": "collections",
                }
            },
            {"$project": {"_id": 1, "collection_id": 1}},
        ],
        "as": "collections",
    }


def _check_collections(sample_dict: dict) -> list[dict[str, str]]:
    """Loop through the provided collection metadata for the sample and
    return the list of references to store (i.e., just the `immutable_id`
    of the collection).

    Raises:
        ValueError: if any of the linked collections cannot be found in
        the database.

    Returns:
        A list of dictionaries with singular key `immutable_id` returning
        the database ID of the collection.

    """
    if sample_dict.get("collections", []):
        for ind, c in enumerate(sample_dict.get("collections", [])):
            query = {}
            query.update(c)
            if "immutable_id" in c:
                query["_id"] = ObjectId(query.pop("immutable_id"))
            result = flask_mongo.db.collections.find_one({**query, **get_default_permissions()})
            if not result:
                raise ValueError(f"No collection found matching request: {c}")
            sample_dict["collections"][ind] = {"immutable_id": result["_id"]}

    return sample_dict.get("collections", []) or []


def get_samples():
    return jsonify({"status": "success", "samples": list(get_samples_summary())})


get_samples.methods = ("GET",)  # type: ignore


def search_items():
    """Perform free text search on items and return the top results.
    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of  (default 100)
        types: If None, search all types of items. Otherwise, a list of strings
               giving the types to consider. (e.g. ["samples","starting_materials"])

    Returns:
        response list of dictionaries containing the matching items in order of
        descending match score.
    """

    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    types = request.args.get("types", default=None)
    if isinstance(types, str):
        types = types.split(",")  # should figure out how to parse as list automatically

    match_obj = {
        "$text": {"$search": query},
        **get_default_permissions(user_only=False),
    }
    if types is not None:
        match_obj["type"] = {"$in": types}

    cursor = flask_mongo.db.items.aggregate(
        [
            {"$match": match_obj},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": nresults},
            {
                "$project": {
                    "_id": 0,
                    "type": 1,
                    "item_id": 1,
                    "name": 1,
                    "chemform": 1,
                    "refcode": 1,
                }
            },
        ]
    )

    return jsonify({"status": "success", "items": list(cursor)}), 200


search_items.methods = ("GET",)  # type: ignore


def _create_sample(sample_dict: dict, copy_from_item_id: Optional[str] = None) -> tuple[dict, int]:
    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            dict(
                status="error",
                message="Unable to create new item without user authentication.",
                item_id=sample_dict["item_id"],
            ),
            401,
        )

    if copy_from_item_id:
        copied_doc = flask_mongo.db.items.find_one({"item_id": copy_from_item_id})

        LOGGER.debug(f"Copying from pre-existing item {copy_from_item_id} with data:\n{copied_doc}")
        if not copied_doc:
            return (
                dict(
                    status="error",
                    message=f"Request to copy item with id {copy_from_item_id} failed because item could not be found.",
                    item_id=sample_dict["item_id"],
                ),
                404,
            )

        # the provided item_id, name, and date take precedence over the copied parameters, if provided
        try:
            copied_doc["item_id"] = sample_dict["item_id"]
        except KeyError:
            return (
                dict(
                    status="error",
                    message=f"Request to copy item with id {copy_from_item_id} to new item failed because the target new item_id was not provided.",
                ),
                400,
            )

        copied_doc["name"] = sample_dict.get("name")
        copied_doc["date"] = sample_dict.get("date")

        # any provided constituents will be added to the synthesis information table in
        # addition to the constituents copied from the copy_from_item_id, avoiding duplicates
        if copied_doc["type"] == "samples":
            existing_consituent_ids = [
                constituent["item"].get("item_id", None)
                for constituent in copied_doc["synthesis_constituents"]
            ]
            copied_doc["synthesis_constituents"] += [
                constituent
                for constituent in sample_dict.get("synthesis_constituents", [])
                if constituent["item"].get("item_id") is None
                or constituent["item"].get("item_id") not in existing_consituent_ids
            ]
            sample_dict = copied_doc

        elif copied_doc["type"] == "cells":
            for component in (
                "positive_electrode",
                "negative_electrode",
                "electrolyte",
            ):
                if copied_doc.get(component):
                    existing_consituent_ids = [
                        constituent["item"].get("item_id", None)
                        for constituent in copied_doc[component]
                    ]
                    copied_doc[component] += [
                        constituent
                        for constituent in sample_dict.get(component, [])
                        if constituent["item"].get("item_id", None) is None
                        or constituent["item"].get("item_id") not in existing_consituent_ids
                    ]

            sample_dict = copied_doc

    try:
        # If passed collection data, dereference it and check if the collection exists
        sample_dict["collections"] = _check_collections(sample_dict)
    except ValueError as exc:
        return (
            dict(
                status="error",
                message=f"Unable to create new item {sample_dict['item_id']!r} inside non-existent collection(s): {exc}",
                item_id=sample_dict["item_id"],
            ),
            401,
        )

    sample_dict.pop("refcode", None)
    type = sample_dict["type"]
    if type not in ITEM_MODELS:
        raise RuntimeError("Invalid type")
    model = ITEM_MODELS[type]
    schema = model.schema()

    new_sample = {k: sample_dict[k] for k in schema["properties"] if k in sample_dict}

    if CONFIG.TESTING:
        # Set fake ID to ObjectId("000000000000000000000000") so a dummy user can be created
        # locally for testing creator UI elements
        new_sample["creator_ids"] = [24 * "0"]
        new_sample["creators"] = [
            {
                "display_name": "Public testing user",
                "contact_email": "datalab@odbx.science",
            }
        ]
    else:
        new_sample["creator_ids"] = [current_user.person.immutable_id]
        new_sample["creators"] = [
            {
                "display_name": current_user.person.display_name,
                "contact_email": current_user.person.contact_email,
            }
        ]

    # check to make sure that item_id isn't taken already
    if flask_mongo.db.items.find_one({"item_id": sample_dict["item_id"]}):
        return (
            dict(
                status="error",
                message=f"item_id_validation_error: {sample_dict['item_id']!r} already exists in database.",
                item_id=new_sample["item_id"],
            ),
            409,  # 409: Conflict
        )

    # Generate a unique refcode for the sample
    new_sample["refcode"] = generate_unique_refcode()

    new_sample["date"] = new_sample.get("date", datetime.datetime.now())
    try:
        data_model: Item = model(**new_sample)

    except ValidationError as error:
        return (
            dict(
                status="error",
                message=f"Unable to create new item with ID {new_sample['item_id']}: {str(error)}.",
                item_id=new_sample["item_id"],
                output=str(error),
            ),
            400,
        )

    # Do not store the fields `collections` or `creators` in the dataabse as these should be populated
    # via joins for a specific query.
    # TODO: encode this at the model level, via custom schema properties or hard-coded `.store()` methods
    # the `Entry` model.
    result = flask_mongo.db.items.insert_one(data_model.dict(exclude={"creators", "collections"}))
    if not result.acknowledged:
        return (
            dict(
                status="error",
                message=f"Failed to add new item {new_sample['item_id']!r} to database.",
                item_id=new_sample["item_id"],
                output=result.raw_result,
            ),
            400,
        )

    sample_list_entry = {
        "refcode": data_model.refcode,
        "item_id": data_model.item_id,
        "nblocks": 0,
        "date": data_model.date,
        "name": data_model.name,
        "creator_ids": data_model.creator_ids,
        # TODO: This workaround for creators & collections is still gross, need to figure this out properly
        "creators": [json.loads(c.json(exclude_unset=True)) for c in data_model.creators]
        if data_model.creators
        else [],
        "collections": [
            json.loads(c.json(exclude_unset=True, exclude_none=True))
            for c in data_model.collections
        ]
        if data_model.collections
        else [],
        "type": data_model.type,
    }

    # hack to let us use _create_sample() for equipment too. We probably want to make
    # a more general create_item() to more elegantly handle different returns.
    if data_model.type == "equipment":
        sample_list_entry["location"] = data_model.location

    data = (
        {
            "status": "success",
            "item_id": data_model.item_id,
            "sample_list_entry": sample_list_entry,
        },
        201,  # 201: Created
    )

    return data


def create_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    if "new_sample_data" in request_json:
        response, http_code = _create_sample(
            request_json["new_sample_data"], request_json.get("copy_from_item_id")
        )
    else:
        response, http_code = _create_sample(request_json)

    return jsonify(response), http_code


create_sample.methods = ("POST",)  # type: ignore


def create_samples():
    """attempt to create multiple samples at once.
    Because each may result in success or failure, 207 is returned along with a
    json field containing all the individual http_codes"""

    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable

    sample_jsons = request_json["new_sample_datas"]
    copy_from_item_ids = request_json.get("copy_from_item_ids")

    if copy_from_item_ids is None:
        copy_from_item_ids = [None] * len(sample_jsons)

    outputs = [
        _create_sample(sample_json, copy_from_item_id)
        for sample_json, copy_from_item_id in zip(sample_jsons, copy_from_item_ids)
    ]
    responses, http_codes = zip(*outputs)

    statuses = [response["status"] for response in responses]
    nsuccess = statuses.count("success")
    nerror = statuses.count("error")

    return (
        jsonify(
            nsuccess=nsuccess,
            nerror=nerror,
            responses=responses,
            http_codes=http_codes,
        ),
        207,
    )  # 207: multi-status


create_samples.methods = ("POST",)  # type: ignore


def delete_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    item_id = request_json["item_id"]

    result = flask_mongo.db.items.delete_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)}
    )

    if result.deleted_count != 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Authorization required to attempt to delete sample with {item_id=} from the database.",
                }
            ),
            401,
        )
    return (
        jsonify(
            {
                "status": "success",
            }
        ),
        200,
    )


delete_sample.methods = ("POST",)  # type: ignore


def get_item_data(item_id, load_blocks: bool = False):
    """Generates a JSON response for the item with the given `item_id`,
    additionally resolving relationships to files and other items.

    Parameters:
       load_blocks: Whether to regenerate any data blocks associated with this
           sample (i.e., create the Python object corresponding to the block and
           call its render function).

    """

    # retrieve the entry from the database:
    cursor = flask_mongo.db.items.aggregate(
        [
            {
                "$match": {
                    "item_id": item_id,
                    **get_default_permissions(user_only=False),
                }
            },
            {"$lookup": creators_lookup()},
            {"$lookup": collections_lookup()},
            {"$lookup": files_lookup()},
        ],
    )

    try:
        doc = list(cursor)[0]
    except IndexError:
        doc = None

    if not doc or (
        not current_user.is_authenticated
        and not CONFIG.TESTING
        and not doc["type"] == "starting_materials"
    ):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"No matching item {item_id=} with current authorization.",
                }
            ),
            404,
        )

    # determine the item type and validate according to the appropriate schema
    try:
        ItemModel = ITEM_MODELS[doc["type"]]
    except KeyError:
        if "type" in doc:
            raise KeyError(f"Item {item_id=} has invalid type: {doc['type']}")
        else:
            raise KeyError(f"Item {item_id=} has no type field in document.")

    doc = ItemModel(**doc)
    if load_blocks:
        doc.blocks_obj = reserialize_blocks(doc.display_order, doc.blocks_obj)

    # find any documents with relationships that mention this document
    relationships_query_results = flask_mongo.db.items.find(
        filter={
            "$or": [
                {"relationships.item_id": doc.item_id},
                {"relationships.refcode": doc.refcode},
                {"relationships.immutable_id": doc.immutable_id},
            ]
        },
        projection={
            "item_id": 1,
            "refcode": 1,
            "relationships": {
                "$elemMatch": {
                    "$or": [
                        {"item_id": doc.item_id},
                        {"refcode": doc.refcode},
                    ],
                },
            },
        },
    )

    # loop over and collect all 'outer' relationships presented by other items
    incoming_relationships: Dict[RelationshipType, Set[str]] = {}
    for d in relationships_query_results:
        for k in d["relationships"]:
            if k["relation"] not in incoming_relationships:
                incoming_relationships[k["relation"]] = set()
            incoming_relationships[k["relation"]].add(
                d["item_id"] or d["refcode"] or d["immutable_id"]
            )

    # loop over and aggregate all 'inner' relationships presented by this item
    inlined_relationships: Dict[RelationshipType, Set[str]] = {}
    if doc.relationships is not None:
        inlined_relationships = {
            relation: {
                d.item_id or d.refcode or d.immutable_id
                for d in doc.relationships
                if d.relation == relation
            }
            for relation in RelationshipType
        }

    # reunite parents and children from both directions of the relationships field
    parents = incoming_relationships.get(RelationshipType.CHILD, set()).union(
        inlined_relationships.get(RelationshipType.PARENT, set())
    )
    children = incoming_relationships.get(RelationshipType.PARENT, set()).union(
        inlined_relationships.get(RelationshipType.CHILD, set())
    )

    # Must be exported to JSON first to apply the custom pydantic JSON encoders
    return_dict = json.loads(doc.json(exclude_unset=True))

    # create the files_data dictionary keyed by file ObjectId
    files_data: Dict[ObjectId, Dict] = {
        f["immutable_id"]: f for f in return_dict.get("files") or []
    }

    return jsonify(
        {
            "status": "success",
            "item_id": item_id,
            "item_data": return_dict,
            "files_data": files_data,
            "child_items": sorted(children),
            "parent_items": sorted(parents),
        }
    )


get_item_data.methods = ("GET",)  # type: ignore


def save_item():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable

    item_id = request_json["item_id"]
    updated_data = request_json["data"]

    # These keys should not be updated here and cannot be modified by the user through this endpoint
    for k in (
        "_id",
        "file_ObjectIds",
        "creators",
        "creator_ids",
        "item_id",
        "relationships",
    ):
        if k in updated_data:
            del updated_data[k]

    updated_data["last_modified"] = datetime.datetime.now().isoformat()

    for block_id, block_data in updated_data.get("blocks_obj", {}).items():
        blocktype = block_data["blocktype"]

        block = BLOCK_TYPES.get(blocktype, BLOCK_TYPES["notsupported"]).from_web(block_data)

        updated_data["blocks_obj"][block_id] = block.to_db()

    item = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)}
    )

    if not item:
        return (
            jsonify(
                status="error",
                message=f"Unable to find item with appropriate permissions and {item_id=}.",
            ),
            400,
        )

    if updated_data.get("collections", []):
        try:
            updated_data["collections"] = _check_collections(updated_data)
        except ValueError as exc:
            return (
                dict(
                    status="error",
                    message=f"Cannot update {item_id!r} with missing collections {updated_data['collections']!r}: {exc}",
                    item_id=item_id,
                ),
                401,
            )

    item_type = item["type"]
    item.update(updated_data)

    try:
        item = ITEM_MODELS[item_type](**item).dict()
    except ValidationError as exc:
        return (
            jsonify(
                status="error",
                message=f"Unable to update item {item_id=} ({item_type=}) with new data {updated_data}",
                output=str(exc),
            ),
            400,
        )

    # remove collections and creators and any other reference fields
    item.pop("collections")
    item.pop("creators")

    result = flask_mongo.db.items.update_one(
        {"item_id": item_id},
        {"$set": item},
    )

    if result.matched_count != 1:
        return (
            jsonify(
                status="error",
                message=f"{item_id} item update failed. no subdocument matched",
                output=result.raw_result,
            ),
            400,
        )

    return jsonify(status="success", last_modified=updated_data["last_modified"]), 200


save_item.methods = ("POST",)  # type: ignore


def search_users():
    """Perform free text search on users and return the top results.
    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of  (default 100)

    Returns:
        response list of dictionaries containing the matching items in order of
        descending match score.
    """

    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    types = request.args.get("types", default=None)

    match_obj = {"$text": {"$search": query}}
    if types is not None:
        match_obj["type"] = {"$in": types}

    cursor = flask_mongo.db.users.aggregate(
        [
            {"$match": match_obj},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": nresults},
            {
                "$project": {
                    "_id": 1,
                    "identities": 1,
                    "display_name": 1,
                }
            },
        ]
    )

    return jsonify({"status": "success", "users": list(cursor)}), 200


ENDPOINTS: Dict[str, Callable] = {
    "/samples/": get_samples,
    "/starting-materials/": get_starting_materials,
    "/equipment/": get_equipment_summary,
    "/search-items/": search_items,
    "/search-users/": search_users,
    "/new-sample/": create_sample,
    "/new-samples/": create_samples,
    "/delete-sample/": delete_sample,
    "/get-item-data/<item_id>": get_item_data,
    "/save-item/": save_item,
}
