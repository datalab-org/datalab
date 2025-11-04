import json
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.exceptions import BadRequest

from pydatalab.config import CONFIG
from pydatalab.permissions import active_users_or_get_only
from pydatalab.remote_filesystems import (
    get_directory_structure,
    get_directory_structures,
)


def _check_invalidate_cache(args: dict[str, str]) -> bool | None:
    invalidate_cache: bool | None = None
    if "invalidate_cache" in args:
        invalidate_cache_arg = args.get("invalidate_cache")
        if invalidate_cache_arg not in ("1", "0"):
            raise BadRequest("invalidate_cache must be 0 or 1")
        invalidate_cache = bool(int(invalidate_cache_arg))

    return invalidate_cache


REMOTES = Blueprint("remotes", __name__)


@REMOTES.before_request
@active_users_or_get_only
def _(): ...


@REMOTES.route("/list-remote-directories", methods=["GET"])
@REMOTES.route("/remotes", methods=["GET"])
def list_remote_directories():
    """Returns the most recent directory structures from the server.

    If the cache is missing or is older than some configured time,
    then it will be reconstructed.

    """
    if (
        not (current_user.is_authenticated and current_user.account_status == "active")
        and not CONFIG.TESTING
    ):
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "Listing remote directories requires authentication.",
                }
            ),
            401,
        )

    try:
        invalidate_cache = _check_invalidate_cache(request.args)
    except RuntimeError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Invalid Argument",
                    "detail": str(e),
                }
            ),
            400,
        )

    all_directory_structures = get_directory_structures(
        CONFIG.REMOTE_FILESYSTEMS, invalidate_cache=invalidate_cache
    )

    response = {}
    response["meta"] = {}
    response["meta"]["remotes"] = [json.loads(d.json()) for d in CONFIG.REMOTE_FILESYSTEMS]
    if all_directory_structures:
        oldest_update = min(d["last_updated"] for d in all_directory_structures)
        response["meta"]["oldest_cache_update"] = oldest_update.isoformat()
        response["data"] = all_directory_structures
    return jsonify(response), 200


list_remote_directories.methods = ("GET",)  # type: ignore


@REMOTES.route("/remotes/<path:remote_id>", methods=["GET"])
def get_remote_directory(remote_id: str):
    """Returns the directory structure from the server for the
    given configured remote name.

    """
    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "Listing remote directories requires authentication.",
                }
            ),
            401,
        )

    try:
        invalidate_cache = _check_invalidate_cache(request.args)
    except RuntimeError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Invalid Argument",
                    "detail": str(e),
                }
            ),
            400,
        )

    for d in CONFIG.REMOTE_FILESYSTEMS:
        if remote_id == d.name:
            remote_obj = d
            break
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Found",
                    "detail": f"No remote found with name {remote_id!r}",
                }
            ),
            404,
        )

    directory_structure = get_directory_structure(remote_obj, invalidate_cache=invalidate_cache)

    response: dict[str, Any] = {}
    response["meta"] = {}
    response["meta"]["remote"] = json.loads(d.json())
    response["data"] = directory_structure

    return jsonify(response), 200
