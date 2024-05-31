import os

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, request, send_from_directory
from flask_login import current_user
from pymongo import ReturnDocument
from werkzeug.utils import secure_filename

import pydatalab.mongo
from pydatalab import file_utils
from pydatalab.config import CONFIG
from pydatalab.permissions import active_users_or_get_only, get_default_permissions

FILES = Blueprint("files", __name__)


@FILES.before_request
@active_users_or_get_only
def _(): ...


@FILES.route("/files/<string:file_id>/<string:filename>", methods=["GET"])
def get_file(file_id: str, filename: str):
    try:
        _file_id = ObjectId(file_id)
    except InvalidId:
        # If the ID is invalid, then there will be no results in the database anyway,
        # so just 401
        _file_id = file_id
    if not pydatalab.mongo.flask_mongo.db.files.find_one(
        {"_id": _file_id, **get_default_permissions(user_only=False)}
    ):
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "Authorization required to access file",
                }
            ),
            401,
        )
    path = os.path.join(CONFIG.FILE_DIRECTORY, secure_filename(file_id))
    return send_from_directory(path, filename)


@FILES.route("/upload-file/", methods=["POST"])
def upload():
    """method to upload files to the server
    todo: think more about security, size limits, and about nested folders
    """

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "File upload requires login.",
                }
            ),
            401,
        )

    if len(request.files) == 0:
        return jsonify(error="No file in request"), 400
    if "item_id" not in request.form:
        return jsonify(error="No item id provided in form"), 400
    item_id = request.form["item_id"]
    replace_file_id = request.form["replace_file"]

    if not CONFIG.TESTING:
        creator_id = current_user.person.immutable_id
    else:
        creator_id = ObjectId(24 * "0")

    is_update = replace_file_id and replace_file_id != "null"
    for filekey in request.files:  # pretty sure there is just 1 per request
        file = request.files[
            filekey
        ]  # just a weird thing about the request that comes from uppy. The key is "files[]"
        if is_update:
            file_information = file_utils.update_uploaded_file(file, ObjectId(replace_file_id))
        else:
            file_information = file_utils.save_uploaded_file(
                file, item_ids=[item_id], creator_ids=[creator_id]
            )

    return (
        jsonify(
            {
                "status": "success",
                "file_id": str(file_information["_id"]),
                "file_information": file_information,
                "is_update": is_update,  # true if update, false if new file
            }
        ),
        201,
    )


@FILES.route("/add-remote-file-to-sample/", methods=["POST"])
def add_remote_file_to_sample():
    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "Adding a file to a sample requires login.",
                }
            ),
            401,
        )

    request_json = request.get_json()
    item_id = request_json["item_id"]
    file_entry = request_json["file_entry"]

    if not CONFIG.TESTING:
        creator_id = current_user.person.immutable_id
    else:
        creator_id = ObjectId(24 * "0")

    updated_file_entry = file_utils.add_file_from_remote_directory(
        file_entry, item_id, creator_ids=[creator_id]
    )

    return (
        jsonify(
            {
                "status": "success",
                "file_id": str(updated_file_entry["_id"]),
                "file_information": updated_file_entry,
            }
        ),
        201,
    )


@FILES.route("/delete-file-from-sample/", methods=["POST"])
def delete_file_from_sample():
    """Remove a file from a sample, but don't delete the actual file (for now)"""

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "Adding a file to a sample requires login.",
                }
            ),
            401,
        )

    request_json = request.get_json()

    item_id = request_json["item_id"]
    file_id = ObjectId(request_json["file_id"])
    result = pydatalab.mongo.flask_mongo.db.items.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {"$pull": {"file_ObjectIds": file_id}},
    )
    if result.modified_count != 1:
        return (
            jsonify(
                status="error",
                message=f"Not authorized to perform file removal from sample {item_id=}",
                output=result.raw_result,
            ),
            401,
        )
    updated_file_entry = pydatalab.mongo.flask_mongo.db.files.find_one_and_update(
        {"_id": file_id},
        {"$pull": {"item_ids": item_id}},
        return_document=ReturnDocument.AFTER,
    )

    if not updated_file_entry:
        return (
            jsonify(
                status="error",
                message=f"{item_id} {file_id} delete failed. Something went wrong with the db call to remove sample from file",
            ),
            400,
        )

    return (
        jsonify(
            {
                "status": "success",
                "new_file_obj": {request_json["file_id"]: updated_file_entry},
            }
        ),
        200,
    )


@FILES.route("/delete-file/", methods=["POST"])
def delete_file():
    """delete a data file from the uploads/item_id folder"""

    if not current_user.is_authenticated and not CONFIG.TESTING:
        return (
            jsonify(
                {
                    "status": "error",
                    "title": "Not Authorized",
                    "detail": "Adding a file to a sample requires login.",
                }
            ),
            401,
        )

    request_json = request.get_json()

    item_id = request_json["item_id"]
    filename = request_json["filename"]

    secure_item_id = secure_filename(item_id)
    secure_fname = secure_filename(filename)

    path = os.path.join(CONFIG.FILE_DIRECTORY, secure_item_id, secure_fname)

    if not os.path.isfile(path):
        return (
            jsonify(
                status="error",
                message="Delete failed. file not found: {}".format(path),
            ),
            400,
        )

    result = pydatalab.mongo.flask_mongo.db.items.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {"$pull": {"files": filename}},
        return_document=ReturnDocument.AFTER,
    )
    if result.matched_count != 1:
        return (
            jsonify(
                status="error",
                message=f"{item_id} {filename} delete failed. Something went wrong with the db call. File not deleted.",
                output=result.raw_result,
            ),
            400,
        )
    os.remove(path)

    return jsonify({"status": "success"}), 200
