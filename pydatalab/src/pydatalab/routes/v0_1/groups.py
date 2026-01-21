import json

from flask import Blueprint, jsonify, request

from pydatalab.models.people import Group
from pydatalab.mongo import flask_mongo
from pydatalab.permissions import active_users_or_get_only

GROUPS = Blueprint("groups", __name__)


@GROUPS.before_request
@active_users_or_get_only
def _(): ...


@GROUPS.route("/search/groups", methods=["GET"])
def search_groups():
    """Perform free text search on groups and return the top results.
    GET parameters:
        query: String with the search terms.
        nresults: Maximum number of results (default 100)

    Returns:
        response list of dictionaries containing the matching groups in order of
        descending match score.
    """

    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    match_obj = {"$text": {"$search": query}}

    cursor = flask_mongo.db.groups.aggregate(
        [
            {"$match": match_obj},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": nresults},
            {
                "$project": {
                    "_id": 1,
                    "display_name": 1,
                    "description": 1,
                    "group_id": 1,
                }
            },
        ]
    )
    return jsonify(
        {"status": "success", "data": list(json.loads(Group(**d).json()) for d in cursor)}
    ), 200
