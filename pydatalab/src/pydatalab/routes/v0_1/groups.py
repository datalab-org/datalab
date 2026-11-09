from flask import Blueprint, jsonify, request
from flask_login import current_user

from pydatalab.login import UserRole
from pydatalab.models.people import Group
from pydatalab.mongo import (
    GROUPS_FTS_FIELDS,
    build_search_pipeline,
    flask_mongo,
)
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
        member_only: Whether to only return groups that the current user is a member of
            (default false); admins are always shown all groups.

    Returns:
        response list of dictionaries containing the matching groups in order of
        descending match score.
    """

    query = request.args.get("query", type=str)
    nresults = request.args.get("nresults", default=100, type=int)
    member_only = request.args.get("member_only", default="false").lower() == "true"

    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400

    group_filter = None
    if member_only and not (current_user.is_authenticated and current_user.role == UserRole.ADMIN):
        user_group_ids = []
        if current_user.is_authenticated and current_user.person is not None:
            user_group_ids = [group.immutable_id for group in current_user.person.groups or []]
        group_filter = {"_id": {"$in": user_group_ids}}

    pipeline = build_search_pipeline(query, GROUPS_FTS_FIELDS, permissions=group_filter)
    pipeline.append({"$limit": nresults})
    pipeline.append({"$project": {"_id": 1, "display_name": 1, "description": 1, "group_id": 1}})
    cursor = flask_mongo.db.groups.aggregate(pipeline)

    return jsonify(
        {
            "status": "success",
            "data": [Group(**d).model_dump(mode="json") for d in cursor],
        }
    ), 200
