import datetime
import json
import re
import secrets
from hashlib import sha512

from bson import ObjectId
from bson.errors import InvalidId
from deepdiff import DeepDiff
from flask import Blueprint, jsonify, redirect, request
from flask_login import current_user
from pydantic import ValidationError
from pymongo.command_cursor import CommandCursor
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest, Conflict, NotFound

from pydatalab.apps import BLOCK_TYPES
from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS, ItemVersion
from pydatalab.models.items import Item
from pydatalab.models.relationships import RelationshipType
from pydatalab.models.utils import generate_unique_refcode
from pydatalab.models.versions import (
    CompareVersionsQuery,
    RestoreVersionRequest,
    VersionAction,
)
from pydatalab.mongo import ITEMS_FTS_FIELDS, flask_mongo
from pydatalab.permissions import (
    PUBLIC_USER_ID,
    access_token_or_active_users,
    active_users_or_get_only,
    check_access_token,
    get_default_permissions,
)
from pydatalab.versioning import (
    apply_protected_fields,
    check_version_access,
    get_next_version_number,
    save_version_snapshot,
)

ITEMS = Blueprint("items", __name__)

# item types that should be accessed by anyone with an account
ACCESSIBLE_TYPES = ("equipment", "starting_materials")


@ITEMS.before_request
@active_users_or_get_only
def _(): ...


@ITEMS.route("/equipment/", methods=["GET"])
def get_equipment_summary():
    _project = {
        "_id": 0,
        "item_id": 1,
        "name": 1,
        "type": 1,
        "date": 1,
        "refcode": 1,
        "location": 1,
        "status": 1,
    }

    items = [
        doc
        for doc in flask_mongo.db.items.aggregate(
            [
                {
                    "$match": {
                        "type": "equipment",
                    }
                },
                {"$project": _project},
            ]
        )
    ]
    return jsonify({"status": "success", "items": items})


@ITEMS.route("/starting-materials/", methods=["GET"])
def get_starting_materials():
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
                        "blocks": {"blocktype": 1, "title": 1},
                        "nblocks": {"$size": "$display_order"},
                        "nfiles": {"$size": "$file_ObjectIds"},
                        "date": 1,
                        "chemform": 1,
                        "name": 1,
                        "type": 1,
                        "chemical_purity": 1,
                        "barcode": 1,
                        "refcode": 1,
                        "supplier": 1,
                        "location": 1,
                        "status": 1,
                    }
                },
                {
                    "$sort": {
                        "date": -1,
                    },
                },
            ]
        )
    ]
    return jsonify({"status": "success", "items": items})


get_starting_materials.methods = ("GET",)  # type: ignore


def get_items_summary(match: dict | None = None, project: dict | None = None) -> CommandCursor:
    """Return a summary of item entries that match some criteria.

    Parameters:
        match: A MongoDB aggregation match query to filter the results.
        project: A MongoDB aggregation project query to filter the results, relative
            to the default included below.

    """
    if not match:
        match = {}
    match.update(get_default_permissions(user_only=False))

    _project = {
        "_id": 0,
        "blocks": {"blocktype": 1, "title": 1},
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
        "nfiles": {"$size": "$file_ObjectIds"},
        "characteristic_chemical_formula": 1,
        "type": 1,
        "date": 1,
        "refcode": 1,
        "status": 1,
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


def get_samples_summary(match: dict | None = None, project: dict | None = None) -> CommandCursor:
    """Return a summary of samples/cells entries that match some criteria.

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
        "blocks": {"blocktype": 1, "title": 1},
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
        "nfiles": {"$size": "$file_ObjectIds"},
        "characteristic_chemical_formula": 1,
        "type": 1,
        "date": 1,
        "refcode": 1,
        "status": 1,
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


def creators_lookup() -> dict:
    return {
        "from": "users",
        "let": {"creator_ids": "$creator_ids"},
        "pipeline": [
            {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$creator_ids", []]}]}}},
            {"$addFields": {"__order": {"$indexOfArray": ["$$creator_ids", "$_id"]}}},
            {"$sort": {"__order": 1}},
            {"$project": {"_id": 1, "display_name": 1, "contact_email": 1}},
        ],
        "as": "creators",
    }


def groups_lookup() -> dict:
    return {
        "from": "groups",
        "let": {"group_ids": "$group_ids"},
        "pipeline": [
            {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$group_ids", []]}]}}},
            {"$addFields": {"__order": {"$indexOfArray": ["$$group_ids", "$_id"]}}},
            {"$sort": {"__order": 1}},
            {"$project": {"_id": 1, "display_name": 1, "group_id": 1}},
        ],
        "as": "groups",
    }


def files_lookup() -> dict:
    return {
        "from": "files",
        "localField": "file_ObjectIds",
        "foreignField": "_id",
        "as": "files",
    }


def collections_lookup() -> dict:
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


@ITEMS.route("/samples/", methods=["GET"])
def get_samples():
    return jsonify({"status": "success", "samples": list(get_samples_summary())})


@ITEMS.route("/search-items/", methods=["GET"])
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
        # should figure out how to parse as list automatically
        types = types.split(",")

    pipeline = []

    if isinstance(query, str):
        query = query.strip("'")

    if isinstance(query, str) and query.startswith("%"):
        # Old FTS query style, using MongoDB text indexes
        query = query.lstrip("%")
        query = query.strip("'")
        match_obj = {
            "$text": {"$search": query},
            **get_default_permissions(user_only=False),
        }
        if types is not None:
            match_obj["type"] = {"$in": types}

        pipeline.append({"$match": match_obj})
        pipeline.append({"$sort": {"score": {"$meta": "textScore"}}})
    elif isinstance(query, str) and query.startswith("#"):
        # Plain regex search, without word boundaries or splitting into parts
        query = query.lstrip("#")
        query = query.strip("'")

        match_obj = {
            "$or": [{field: {"$regex": query, "$options": "i"}} for field in ITEMS_FTS_FIELDS]
        }
        match_obj = {"$and": [get_default_permissions(user_only=False), match_obj]}
        if types is not None:
            match_obj["$and"].append({"type": {"$in": types}})

        pipeline.append({"$match": match_obj})

    else:
        # Heuristic + regex search, splitting the query into parts and adding word boundaries
        # depending on length
        def _generate_heuristic_regex_search(query: str, part_length: int = 4) -> dict:
            """Generate a heuristic regex search object for MongoDB that uses
            word boundaries for short parts of the query, but allows matches anywhere.

            Parameters:
                query: The full search query string.
                part_length: The length below which to add a word boundary to the start of the part.

            Returns:
                A MongoDB query object that can be used in a $match stage.

            """
            query_parts = [re.escape(part) for part in query.split(" ") if part.strip()]

            # Add word boundary to short parts to avoid excessive matches, i.e., search start of string
            # for short parts, but allow match anywhere in string for longer parts
            query_parts = [
                f"\\b{part}" if len(part) <= part_length else part for part in query_parts
            ]
            match_obj = {
                "$or": [
                    {"$and": [{field: {"$regex": query, "$options": "i"}} for query in query_parts]}
                    for field in ITEMS_FTS_FIELDS
                ]
            }
            LOGGER.debug(
                "Performing regex search for %s with full search %s", query_parts, match_obj
            )

            return match_obj

        if not query:
            return jsonify({"status": "error", "message": "No query provided."}), 400

        match_obj = _generate_heuristic_regex_search(query)
        match_obj = {"$and": [get_default_permissions(user_only=False), match_obj]}
        if types is not None:
            match_obj["$and"].append({"type": {"$in": types}})

        pipeline.append({"$match": match_obj})

    pipeline.append({"$limit": nresults})
    pipeline.append(
        {
            "$project": {
                "_id": 0,
                "type": 1,
                "item_id": 1,
                "name": 1,
                "chemform": 1,
                "refcode": 1,
            }
        }
    )

    cursor = flask_mongo.db.items.aggregate(pipeline)

    return jsonify({"status": "success", "items": list(cursor)}), 200


def _copy_sample_from_id(sample_dict: dict, copy_from_item_id: str) -> dict:
    copied_doc = flask_mongo.db.items.find_one({"item_id": copy_from_item_id})

    LOGGER.debug("Copying from pre-existing item %s with data:\n%s", copy_from_item_id, copied_doc)
    if not copied_doc:
        raise NotFound(
            f"Request to copy item with id {copy_from_item_id} failed because item could not be found."
        )

    # the provided item_id, name, and date take precedence over the copied parameters, if provided
    try:
        copied_doc["item_id"] = sample_dict["item_id"]
    except KeyError:
        raise BadRequest(
            f"Request to copy item with id {copy_from_item_id} to new item failed because the target new item_id was not provided."
        )

    copied_doc["name"] = sample_dict.get("name")
    copied_doc["date"] = sample_dict.get("date")

    copied_doc.pop("blocks_obj", None)
    copied_doc.pop("display_order", None)
    copied_doc.pop("blocks", None)
    copied_doc.pop("file_ObjectIds", None)

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

        original_collections = sample_dict.get("collections", [])
        sample_dict = copied_doc

        if original_collections:
            sample_dict["collections"] = original_collections

    elif copied_doc["type"] == "cells":
        for component in (
            "positive_electrode",
            "negative_electrode",
            "electrolyte",
        ):
            existing_consituent_ids = [
                constituent["item"].get("item_id", None) for constituent in copied_doc[component]
            ]
            copied_doc[component] += [
                constituent
                for constituent in sample_dict.get(component, [])
                if constituent["item"].get("item_id", None) is None
                or constituent["item"].get("item_id") not in existing_consituent_ids
            ]

        original_collections = sample_dict.get("collections", [])
        sample_dict = copied_doc

        if original_collections:
            sample_dict["collections"] = original_collections

    return sample_dict


def _create_sample(
    sample_dict: dict,
    copy_from_item_id: str | None = None,
    generate_id_automatically: bool = False,
) -> tuple[dict, int]:
    sample_dict["item_id"] = sample_dict.get("item_id")

    if generate_id_automatically and sample_dict["item_id"]:
        raise BadRequest(
            f"Request to create item with {generate_id_automatically=} is incompatible with the provided item data, which has an item_id included (id: {sample_dict['item_id']})"
        )

    if copy_from_item_id:
        sample_dict = _copy_sample_from_id(sample_dict, copy_from_item_id)

    try:
        # If passed collection data, dereference it and check if the collection exists
        sample_dict["collections"] = _check_collections(sample_dict)
    except ValueError as exc:
        raise NotFound(
            f"Unable to create new item {sample_dict['item_id']!r} inside non-existent collection(s) {exc}"
        ) from exc

    sample_dict.pop("refcode", None)  # Refcodes cannot be set manually
    # Check type
    type_ = sample_dict["type"]
    if type_ not in ITEM_MODELS:
        raise BadRequest(f"Invalid type {type_!r}, must be one of {ITEM_MODELS.keys()}")

    model = ITEM_MODELS[type_]

    new_sample = sample_dict.copy()

    if type_ in ACCESSIBLE_TYPES:
        # starting_materials and equipment are open to all in the deploment at this point,
        # so no creators are assigned
        new_sample["creator_ids"] = []
        new_sample["creators"] = []

    elif CONFIG.TESTING and not current_user.is_authenticated:
        # Set fake ID to ObjectId("000000000000000000000000") so a dummy user can be created
        # locally for testing creator UI elements
        new_sample["creator_ids"] = [PUBLIC_USER_ID]
        new_sample["creators"] = [
            {
                "display_name": "Public testing user",
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

    # Check for initialised sharing options, e.g., groups and other creators
    if sample_dict.get("creators"):
        for c in sample_dict["creators"]:
            new_sample["creator_ids"].append(ObjectId(c["immutable_id"]))

    if sample_dict.get("groups"):
        new_sample["group_ids"] = []
        for g in sample_dict["groups"]:
            new_sample["group_ids"].append(ObjectId(g["immutable_id"]))

    # Generate a unique refcode for the sample
    new_sample["refcode"] = generate_unique_refcode()
    if generate_id_automatically:
        new_sample["item_id"] = new_sample["refcode"].split(":")[1]

    # Check to make sure that item_id isn't taken already
    if flask_mongo.db.items.find_one({"item_id": str(sample_dict["item_id"])}):
        raise Conflict(f"Chosen {sample_dict['item_id']=} already exists in database.")

    # Set creation timestamp to now if not provided
    new_sample["date"] = new_sample.get("date", datetime.datetime.now(tz=datetime.timezone.utc))

    # Try to deserialize the item data into the appropriate model
    try:
        data_model: Item = model(**new_sample)

    except ValidationError as error:
        raise BadRequest(
            f"Unable to create new item with ID {new_sample['item_id']}: {new_sample} / {error}"
        )

    # Do not store the fields `collections` or `creators` in the database as these should be populated
    # via joins for a specific query.
    # TODO: encode this at the model level, via custom schema properties or hard-coded `.store()` methods
    # the `Entry` model.
    try:
        result = flask_mongo.db.items.insert_one(
            data_model.dict(exclude={"creators", "collections", "groups"})
        )
    except DuplicateKeyError as error:
        raise Conflict(f"Duplicate key error: {str(error)}.")

    if not result.acknowledged:
        raise BadRequest(f"Failed to add new item {new_sample['item_id']!r} to database.")

    # Save initial version snapshot after successful item creation
    try:
        save_version_snapshot(data_model.refcode, action=VersionAction.CREATED)
    except Exception as e:
        # Log but don't fail the request since item was already created successfully
        LOGGER.error(
            "Failed to save initial version for item %s after creation: %s",
            data_model.item_id,
            str(e),
        )

    # sample_list_entry = {
    #     "refcode": data_model.refcode,
    #     "item_id": data_model.item_id,
    #     "nblocks": 0,
    #     "nfiles": 0,
    #     "date": data_model.date,
    #     "name": data_model.name,
    #     "creator_ids": data_model.creator_ids,
    #     # TODO: This workaround for creators & collections is still gross, need to figure this out properly
    #     "creators": [json.loads(c.json(exclude_unset=True)) for c in data_model.creators]
    #     if data_model.creators
    #     else [],
    #     "collections": [
    #         json.loads(c.json(exclude_unset=True, exclude_none=True))
    #         for c in data_model.collections
    #     ],
    #     "group_ids": data_model.group_ids,
    #     "groups": [
    #         json.loads(c.json(exclude_unset=True, exclude_none=True)) for c in data_model.groups
    #     ]
    #     if data_model.groups
    #     else [],
    #     "type": data_model.type,
    #     "status": data_model.status,
    # }

    # hack to let us use _create_sample() for equipment too. We probably want to make
    # a more general create_item() to more elegantly handle different returns.
    # if data_model.type == "equipment":
    #     sample_list_entry["location"] = data_model.location

    data = {
        "status": "success",
        "item_id": data_model.item_id,
        "sample_list_entry": data_model.dict(),
    }

    return (data, 201)  # 201 Created


@ITEMS.route("/new-sample/", methods=["POST", "PUT"])
def create_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    if "new_sample_data" in request_json:
        response, http_code = _create_sample(
            sample_dict=request_json["new_sample_data"],
            copy_from_item_id=request_json.get("copy_from_item_id"),
            generate_id_automatically=request_json.get("generate_id_automatically", False),
        )
    else:
        response, http_code = _create_sample(request_json)

    return jsonify(response), http_code


@ITEMS.route("/new-samples/", methods=["POST", "PUT"])
def create_samples():
    """attempt to create multiple samples at once.
    Because each may result in success or failure, 207 is returned along with a
    json field containing all the individual http_codes"""

    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable

    sample_jsons = request_json["new_sample_datas"]

    if len(sample_jsons) > CONFIG.MAX_BATCH_CREATE_SIZE:
        return jsonify(
            {
                "status": "error",
                "message": f"Batch size limit exceeded. Maximum allowed: {CONFIG.MAX_BATCH_CREATE_SIZE}, requested: {len(sample_jsons)}",
            }
        ), 400

    copy_from_item_ids = request_json.get("copy_from_item_ids")
    generate_ids_automatically = request_json.get("generate_ids_automatically")

    if copy_from_item_ids is None:
        copy_from_item_ids = [None] * len(sample_jsons)

    outputs = [
        _create_sample(
            sample_dict=sample_json,
            copy_from_item_id=copy_from_item_id,
            generate_id_automatically=generate_ids_automatically,
        )
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


@ITEMS.route("/items/<refcode>/permissions", methods=["PATCH"])
def update_item_permissions(refcode: str):
    """Update the permissions of an item with the given refcode."""

    request_json = request.get_json()
    creator_ids: list[ObjectId] = []
    group_ids: list[ObjectId] = []

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    current_item = flask_mongo.db.items.find_one(
        {"refcode": refcode, **get_default_permissions(user_only=True)},
        {"_id": 1, "creator_ids": 1, "group_ids": 1},
    )  # type: ignore

    if not current_item:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"No valid item found with the given {refcode=}.",
                }
            ),
            401,
        )

    current_creator_ids = current_item["creator_ids"]

    creators_requested = False
    groups_requested = False

    if "creators" in request_json and request_json["creators"] is not None:
        creators_requested = True
        new_creators = request_json["creators"]
        if not isinstance(new_creators, list):
            raise RuntimeError("Invalid creators list provided in request.")

        creator_ids = [
            ObjectId(creator.get("immutable_id", None))
            for creator in request_json["creators"]
            if creator.get("immutable_id", None) is not None
        ]

    if "groups" in request_json and request_json["groups"] is not None:
        groups_requested = True
        new_groups = request_json["groups"]
        if not isinstance(new_groups, list):
            raise RuntimeError("Invalid groups list provided in request.")

        group_ids = [
            ObjectId(group.get("immutable_id", None))
            for group in request_json["groups"]
            if group.get("immutable_id", None) is not None
        ]

    if not groups_requested and not creators_requested:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No valid creator or group IDs found in the request.",
                }
            ),
            400,
        )

    # Validate all creator IDs are present in the database
    if creator_ids:
        found_creator_ids = [
            d for d in flask_mongo.db.users.find({"_id": {"$in": creator_ids}}, {"_id": 1})
        ]  # type: ignore
        if len(found_creator_ids) != len(creator_ids):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "One or more creator IDs not found in the database.",
                    }
                ),
                400,
            )

    if group_ids:
        # Validate all group IDs are present in the database
        found_group_ids = [
            d for d in flask_mongo.db.groups.find({"_id": {"$in": group_ids}}, {"_id": 1})
        ]  # type: ignore
        if len(found_group_ids) != len(group_ids):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "One or more group IDs not found in the database.",
                    }
                ),
                400,
            )

    if creator_ids:
        # Make sure a user cannot remove their own access to an item
        current_user_id = current_user.person.immutable_id
        try:
            creator_ids.remove(current_user_id)
        except ValueError:
            pass
        creator_ids.insert(0, current_user_id)

        # The first ID in the creator list takes precedence; always make sure this is included to avoid orphaned items
        if current_creator_ids:
            base_owner = current_creator_ids[0]
            try:
                creator_ids.remove(base_owner)
            except ValueError:
                pass
            creator_ids.insert(0, base_owner)

    LOGGER.warning(
        "Setting permissions for item %s to %s (creators) / %s (groups)",
        refcode,
        creator_ids,
        group_ids,
    )

    set_op = {}
    if creators_requested:
        set_op["creator_ids"] = creator_ids
    if groups_requested:
        set_op["group_ids"] = group_ids

    LOGGER.debug("Updating item %s with set op: %s", refcode, set_op)

    result = flask_mongo.db.items.update_one(
        {"refcode": refcode, **get_default_permissions(user_only=True)}, {"$set": set_op}
    )

    if result.modified_count != 1:
        return jsonify(
            {
                "status": "error",
                "message": "Failed to update permissions: you cannot remove yourself or the base owner as a creator.",
            }
        ), 400

    return jsonify({"status": "success"}), 200


@ITEMS.route("/items/<refcode>/issue-access-token", methods=["POST"])
def issue_physical_token(refcode: str):
    """Issue a token that will give semi-permanent access to an
    item with this refcode. This should be used when generating
    physical labels to attach to a container.

    """

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    current_item = flask_mongo.db.items.find_one(
        {"refcode": refcode, **get_default_permissions(user_only=True)},
        {"refcode": 1},
    )

    if not current_item:
        return jsonify(
            {
                "status": "error",
                "message": f"No valid item found with the given {refcode=}.",
            }
        ), 404

    token = secrets.token_urlsafe(16)
    access_document = {
        "token": sha512(token.encode("utf-8")).hexdigest(),
        "refcode": refcode,
        "user": ObjectId(current_user.id),
        "active": True,
        "created_at": datetime.datetime.now(tz=datetime.timezone.utc),
        "expires_at": None,
        "version": 1,
        "type": "access_token",
    }

    try:
        result = flask_mongo.db.api_keys.insert_one(access_document)
        if not result.inserted_id:
            return jsonify(
                {"status": "error", "message": "Unknown error generating token for item."}
            ), 500
    except Exception as e:
        LOGGER.error("Error inserting access token: %s", e)
        return jsonify(
            {"status": "error", "message": "Database error generating token for item."}
        ), 500

    return jsonify({"status": "success", "token": token}), 201


@ITEMS.route("/delete-sample/", methods=["POST"])
def delete_sample():
    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable
    item_id = request_json["item_id"]

    item = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=True, deleting=True)},
        {"refcode": 1},
    )

    if not item:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Authorization required to attempt to delete sample with {item_id=} from the database.",
                }
            ),
            401,
        )

    result = flask_mongo.db.items.delete_one(
        {"item_id": item_id, **get_default_permissions(user_only=True, deleting=True)}
    )

    if result.deleted_count != 1:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to delete item with {item_id=}.",
                }
            ),
            400,
        )

    flask_mongo.db.api_keys.delete_many({"refcode": item["refcode"], "type": "access_token"})

    return jsonify({"status": "success"}), 200


@ITEMS.route("/items/<refcode>", methods=["GET"])
@access_token_or_active_users
def get_item_by_refcode(refcode: str, elevate_permissions: bool = False):
    return get_item_data(refcode=refcode, elevate_permissions=elevate_permissions)


@ITEMS.route("/get-item-data/<item_id>", methods=["GET"])
@active_users_or_get_only
def get_item_by_id(item_id: str):
    return get_item_data(item_id=item_id, elevate_permissions=False)


def get_item_data(
    item_id: str | None = None, refcode: str | None = None, elevate_permissions: bool = False
):
    """Generates a JSON response for the item with the given `item_id`,
    or `refcode` additionally resolving relationships to files and other items.
    """

    redirect_to_ui = bool(request.args.get("redirect-to-ui", default=False, type=json.loads))
    access_token = request.args.get("at")
    if refcode and redirect_to_ui and CONFIG.APP_URL:
        redirect_url = f"{CONFIG.APP_URL}/items/{refcode}"
        if access_token:
            redirect_url += f"?at={access_token}"
        return redirect(redirect_url, code=307)

    if item_id:
        match = {"item_id": item_id}
    elif refcode:
        if len(refcode.split(":")) != 2:
            refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

        match = {"refcode": refcode}
    else:
        raise BadRequest("No item_id or refcode provided.")

    # retrieve the entry from the database:
    cursor = flask_mongo.db.items.aggregate(
        [
            {
                "$match": {
                    **match,
                    **get_default_permissions(
                        user_only=False, elevate_permissions=elevate_permissions
                    ),
                }
            },
            {"$lookup": creators_lookup()},
            {"$lookup": groups_lookup()},
            {"$lookup": collections_lookup()},
            {"$lookup": files_lookup()},
        ],
    )

    try:
        doc = list(cursor)[0]
    except IndexError:
        doc = None

    if not doc:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"No matching items for {match=} with current authorization.",
                }
            ),
            404,
        )

    # determine the item type and validate according to the appropriate schema
    try:
        ItemModel = ITEM_MODELS[doc["type"]]
    except KeyError:
        if "type" in doc:
            raise BadRequest(f"Item {item_id=} has invalid type: {doc['type']}")
        else:
            raise BadRequest(f"Item {item_id=} has no type field in document.")

    doc = ItemModel(**doc)

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
    incoming_relationships: dict[RelationshipType, set[str]] = {}
    for d in relationships_query_results:
        for k in d["relationships"]:
            if k["relation"] not in incoming_relationships:
                incoming_relationships[k["relation"]] = set()
            incoming_relationships[k["relation"]].add(
                d["item_id"] or d["refcode"] or d["immutable_id"]
            )

    # loop over and aggregate all 'inner' relationships presented by this item
    inlined_relationships: dict[RelationshipType, set[str]] = {}
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

    if item_id is None:
        item_id = return_dict["item_id"]

    return jsonify(
        {
            "status": "success",
            "item_id": item_id,
            "item_data": return_dict,
            "child_items": sorted(children),
            "parent_items": sorted(parents),
        }
    )


# --- VERSION CONTROL ENDPOINTS ---


@ITEMS.route("/items/<refcode>/versions/", methods=["GET"])
def list_versions(refcode):
    """List all saved versions for an item, with metadata.

    Requires read access to the item.
    """
    # Check if user has access to the item (read access)
    has_access, _ = check_version_access(refcode, user_only=False)
    if not has_access:
        return jsonify(
            {"status": "error", "message": "Item not found or insufficient permissions"}
        ), 404

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    versions = list(
        flask_mongo.db.item_versions.find(
            {"refcode": refcode},
            {
                "_id": 1,
                "timestamp": 1,
                "user_id": 1,
                "datalab_version": 1,
                "version": 1,
                "action": 1,
                "restored_from_version": 1,
                "data.version": 1,
            },
        ).sort("version", -1)
    )
    for v in versions:
        v["_id"] = str(v["_id"])
    return jsonify({"status": "success", "versions": versions}), 200


@ITEMS.route("/items/<refcode>/versions/<version_id>/", methods=["GET"])
def get_version(refcode, version_id):
    """Get the full snapshot of an item at a specific version.

    Requires read access to the item.
    """
    # Check if user has access to the item (read access)
    has_access, _ = check_version_access(refcode, user_only=False)
    if not has_access:
        return jsonify(
            {"status": "error", "message": "Item not found or insufficient permissions"}
        ), 404

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    try:
        version_object_id = ObjectId(version_id)
    except (InvalidId, TypeError):
        return jsonify({"status": "error", "message": f"Invalid version_id: {version_id}"}), 400

    version = flask_mongo.db.item_versions.find_one({"_id": version_object_id, "refcode": refcode})
    if not version:
        return jsonify({"status": "error", "message": "Version not found"}), 404
    version["_id"] = str(version["_id"])
    return jsonify({"status": "success", "version": version}), 200


@ITEMS.route("/items/<refcode>/compare-versions/", methods=["GET"])
def compare_versions(refcode):
    """Compare two versions of an item and return their differences, including version numbers.

    Requires read access to the item.
    """
    # Check if user has access to the item (read access)
    has_access, _ = check_version_access(refcode, user_only=False)
    if not has_access:
        return jsonify(
            {"status": "error", "message": "Item not found or insufficient permissions"}
        ), 404

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    # Validate query parameters using Pydantic model
    try:
        query_params = CompareVersionsQuery(
            v1=request.args.get("v1", ""), v2=request.args.get("v2", "")
        )
    except ValidationError as exc:
        return jsonify(
            {"status": "error", "message": "Invalid query parameters", "errors": exc.errors()}
        ), 400

    try:
        v1_object_id = ObjectId(query_params.v1)
        v2_object_id = ObjectId(query_params.v2)
    except (InvalidId, TypeError) as e:
        return jsonify({"status": "error", "message": f"Invalid version ID format: {str(e)}"}), 400

    v1 = flask_mongo.db.item_versions.find_one({"_id": v1_object_id, "refcode": refcode})
    v2 = flask_mongo.db.item_versions.find_one({"_id": v2_object_id, "refcode": refcode})
    if not v1 or not v2:
        return jsonify({"status": "error", "message": "One or both versions not found"}), 404

    # Use DeepDiff for proper nested structure comparison
    # This handles nested dicts, lists, type changes, and provides detailed change information
    deep_diff = DeepDiff(
        v1["data"],
        v2["data"],
        ignore_order=False,  # Preserve list order in comparisons
        verbose_level=2,  # Include detailed change information
    )

    # Convert DeepDiff result to a JSON-serializable dict
    diff = json.loads(deep_diff.to_json()) if deep_diff else {}

    return jsonify(
        {
            "status": "success",
            "diff": diff,
            "v1_version": v1.get("version"),
            "v2_version": v2.get("version"),
            "v1_timestamp": v1.get("timestamp"),
            "v2_timestamp": v2.get("timestamp"),
        }
    ), 200


@ITEMS.route("/items/<refcode>/restore-version/", methods=["POST"])
def restore_version(refcode):
    """Restore an item to a previous version.

    Protected fields that cannot be restored (to maintain data integrity):
    - refcode: Immutable identifier
    - _id: Database primary key
    - immutable_id: Database ObjectId reference
    - creator_ids: Ownership/permissions information
    - file_ObjectIds: File attachments managed separately
    - version: Always increments forward to prevent collisions
    """
    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    # Validate request body using Pydantic model
    try:
        restore_request = RestoreVersionRequest(**request.get_json())
    except ValidationError as exc:
        return jsonify(
            {"status": "error", "message": "Invalid request body", "errors": exc.errors()}
        ), 400

    try:
        version_object_id = ObjectId(restore_request.version_id)
    except (InvalidId, TypeError):
        return jsonify(
            {"status": "error", "message": f"Invalid version_id: {restore_request.version_id}"}
        ), 400

    # Check permissions - user must have write access
    current_item = flask_mongo.db.items.find_one(
        {"refcode": refcode, **get_default_permissions(user_only=True)}
    )
    if not current_item:
        return jsonify(
            {"status": "error", "message": "Item not found or insufficient permissions"}
        ), 404

    version = flask_mongo.db.item_versions.find_one({"_id": version_object_id, "refcode": refcode})
    if not version:
        return jsonify({"status": "error", "message": "Version not found"}), 404

    restored_data = version["data"].copy()

    # Protect critical fields from being overwritten during restore
    restored_data = apply_protected_fields(restored_data, current_item)

    # Ensure type consistency
    if restored_data.get("type") != current_item.get("type"):
        return jsonify(
            {
                "status": "error",
                "message": f"Cannot restore version with different type. Current: {current_item.get('type')}, Version: {restored_data.get('type')}",
            }
        ), 400

    # Atomically get the next version number (used for both version in item_versions and item.version)
    next_version_number = get_next_version_number(refcode)

    # Update metadata to reflect the restore action
    restored_data["version"] = next_version_number
    restored_data["last_modified"] = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    # Validate restored data against the item model
    item_type = current_item["type"]
    if item_type not in ITEM_MODELS:
        return jsonify({"status": "error", "message": f"Invalid item type: {item_type}"}), 400

    try:
        # Validate using the appropriate model
        ITEM_MODELS[item_type](**restored_data)
    except ValidationError as exc:
        return jsonify(
            {
                "status": "error",
                "message": f"Restored data failed validation: {str(exc)}",
                "output": str(exc),
            }
        ), 400

    # Perform the restore first
    flask_mongo.db.items.update_one({"refcode": refcode}, {"$set": restored_data})

    # Extract user information for hybrid storage approach
    user_id = None
    if current_user.is_authenticated:
        user_id = current_user.person.immutable_id

    # Get the software version
    from pydatalab import __version__

    software_version = __version__

    # Save the RESTORED state as a new version snapshot (after restore)
    restored_version_entry = {
        "refcode": refcode,
        "version": next_version_number,
        "timestamp": datetime.datetime.now(tz=datetime.timezone.utc),
        "action": VersionAction.RESTORED,  # Audit trail: this is a restored version
        "restored_from_version": version_object_id,  # Track which version was restored from (ObjectId)
        "user_id": user_id,  # ObjectId for efficient querying
        "datalab_version": software_version,
        "data": restored_data,  # Store the complete snapshot of the restored state
    }

    # Validate with Pydantic before inserting
    try:
        validated_restored_version = ItemVersion(**restored_version_entry)
    except ValidationError as exc:
        LOGGER.error(
            "Restored version validation failed for item %s: %s",
            refcode,
            str(exc),
        )
        return jsonify(
            {
                "status": "error",
                "message": f"Restored version data validation failed: {str(exc)}",
                "output": str(exc),
            }
        ), 400

    # Insert validated data
    flask_mongo.db.item_versions.insert_one(
        validated_restored_version.dict(by_alias=True, exclude_none=True)
    )

    return jsonify(
        {
            "status": "success",
            "restored_version": restore_request.version_id,
            "new_version_number": next_version_number,
        }
    ), 200


@ITEMS.route("/items/<refcode>/versions/<version_id>/", methods=["DELETE"])
def delete_version(refcode, version_id):
    """Delete a specific version.

    Requires write access to the item.
    """
    # Check if user has write access to the item (write access required)
    has_access, _ = check_version_access(refcode, user_only=True)
    if not has_access:
        return jsonify(
            {"status": "error", "message": "Item not found or insufficient permissions"}
        ), 404

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    try:
        version_object_id = ObjectId(version_id)
    except (InvalidId, TypeError):
        return jsonify({"status": "error", "message": f"Invalid version_id: {version_id}"}), 400

    result = flask_mongo.db.item_versions.delete_one({"_id": version_object_id, "refcode": refcode})
    if result.deleted_count == 1:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Version not found"}), 404


@ITEMS.route("/items/<refcode>/save-version/", methods=["POST"])
def save_version(refcode):
    """Manually save the current state of an item as a version snapshot with an incremental version number."""
    response, status_code = save_version_snapshot(
        refcode,
        action=VersionAction.MANUAL_SAVE,
        permission_filter=get_default_permissions(user_only=False),
    )
    return jsonify(response), status_code


# --- END VERSION CONTROL ENDPOINTS ---


@ITEMS.route("/save-item/", methods=["POST"])
def save_item():
    """Update an existing item with new data provided in the request body."""

    request_json = request.get_json()  # noqa: F821 pylint: disable=undefined-variable

    if "item_id" not in request_json:
        raise BadRequest(
            "`/save-item/` endpoint requires 'item_id' to be passed in JSON request body"
        )

    if "data" not in request_json:
        raise BadRequest("`/save-item/` endpoint requires 'data' to be passed in JSON request body")

    item_id = str(request_json["item_id"])
    updated_data = request_json["data"]

    # These keys should not be updated here and cannot be modified by the user through this endpoint
    for k in (
        "_id",
        "file_ObjectIds",
        "files",
        "creators",
        "creator_ids",
        "groups",
        "group_ids",
        "item_id",
        "relationships",
    ):
        if k in updated_data:
            del updated_data[k]

    updated_data["last_modified"] = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    for block_id, block_data in updated_data.get("blocks_obj", {}).items():
        blocktype = block_data["blocktype"]

        block = BLOCK_TYPES.get(blocktype, BLOCK_TYPES["notsupported"]).from_web(block_data)

        updated_data["blocks_obj"][block_id] = block.to_db()

    # Bit of a hack for now: starting materials and equipment should be editable by anyone,
    # so we adjust the query above to be more permissive when the user is requesting such an item
    # but before returning we need to check that the actual item did indeed have that type
    item = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=False)}
    )

    if not item:
        return (
            jsonify(
                status="error",
                message=f"Unable to find item with appropriate permissions and {item_id=}.",
            ),
            404,
        )

    # Store refcode for version saving after successful update
    refcode = item.get("refcode")
    if not refcode:
        return (
            jsonify(
                status="error",
                message=f"Item {item_id} does not have a refcode.",
            ),
            400,
        )

    # Increment version number on the item itself
    updated_data["version"] = item.get("version", 0) + 1

    user_only = item["type"] not in ("starting_materials", "equipment")

    item = flask_mongo.db.items.find_one(
        {"item_id": item_id, **get_default_permissions(user_only=user_only)}
    )

    if not item:
        return (
            jsonify(
                status="error",
                message=f"Unable to find item with appropriate permissions and {item_id=}.",
            ),
            404,
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

    # Update the item FIRST (transaction safety: item update before version save)
    result = flask_mongo.db.items.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
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

    # Now save a version AFTER successful item update
    # If this fails, we log but don't fail the request since item was already saved
    try:
        save_version_resp_dict, save_version_status = save_version_snapshot(
            refcode, action=VersionAction.MANUAL_SAVE
        )
        if save_version_status != 200:
            LOGGER.error(
                "Failed to save version for item %s after successful update: %s",
                item_id,
                save_version_resp_dict,
            )
    except Exception as e:
        LOGGER.error(
            "Exception while saving version for item %s after successful update: %s",
            item_id,
            str(e),
        )

    return jsonify(status="success", last_modified=updated_data["last_modified"]), 200


@ITEMS.route("/items/<refcode>/access-token-info", methods=["GET"])
def get_access_token_info(refcode: str):
    """Get information about existing access token for this item (if any).

    Returns token info (with masked token) if user has permissions to this item.
    """
    access_token = request.args.get("at")
    if access_token and check_access_token(refcode, access_token):
        pass
    elif not (current_user.is_authenticated):
        return jsonify({"status": "error", "message": "Authentication required."}), 401

    if len(refcode.split(":")) != 2:
        refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{refcode}"

    current_item = flask_mongo.db.items.find_one(
        {"refcode": refcode, **get_default_permissions(user_only=True)},
        {"refcode": 1},
    )

    if not current_item:
        return jsonify(
            {
                "status": "error",
                "message": f"No valid item found with the given {refcode=}.",
            }
        ), 404

    existing_token = flask_mongo.db.api_keys.find_one(
        {"refcode": refcode, "active": True, "type": "access_token"},
        {"token": 1, "created_at": 1, "user": 1},
    )

    if existing_token:
        token_hash = existing_token["token"]
        masked_token = token_hash[:8] + "..." + token_hash[-8:]

        user_info = None
        if existing_token.get("user"):
            user_doc = flask_mongo.db.users.find_one(
                {"_id": existing_token["user"]}, {"display_name": 1, "contact_email": 1}
            )
            if user_doc:
                user_info = {
                    "display_name": user_doc.get("display_name"),
                    "contact_email": user_doc.get("contact_email"),
                }

        return jsonify(
            {
                "status": "success",
                "has_token": True,
                "token_info": {
                    "token": masked_token,
                    "created_at": existing_token["created_at"],
                    "created_by": str(existing_token["user"]),
                    "created_by_info": user_info,
                },
            }
        ), 200
    else:
        return jsonify({"status": "success", "has_token": False}), 200
