import os
from typing import Callable, Dict

from bson import ObjectId
from flask import jsonify, request, send_from_directory
from pymongo import ReturnDocument
from werkzeug.utils import secure_filename

import pydatalab.mongo
from pydatalab import file_utils
from pydatalab.config import CONFIG


def get_file(file_id, filename):
    path = os.path.join(CONFIG.FILE_DIRECTORY, file_id)

    print("retrieving file: {} from {}".format(filename, path))
    return send_from_directory(path, filename)


def upload():
    """method to upload files to the server
    todo: think more about security, size limits, and about nested folders
    """
    # print("uploaded files:")
    # print(request.files)
    # print(request.form)
    if len(request.files) == 0:
        return jsonify(error="No file in request"), 400
    if "sample_id" not in request.form == 0:
        return jsonify(error="No sample id provided in form"), 400
    sample_id = request.form["sample_id"]
    replace_file_id = request.form["replace_file"]

    is_update = replace_file_id and replace_file_id != "null"
    for filekey in request.files:  # pretty sure there is just 1 per request
        file = request.files[
            filekey
        ]  # just a weird thing about the request that comes from uppy. The key is "files[]"
        if is_update:
            file_information = file_utils.update_uploaded_file(file, ObjectId(replace_file_id))
        else:
            file_information = file_utils.save_uploaded_file(file, sample_ids=[sample_id])

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


upload.methods = ("POST",)  # type: ignore


def add_remote_file_to_sample():
    print("add_remote_file_to_sample called")
    request_json = request.get_json()
    sample_id = request_json["sample_id"]
    file_entry = request_json["file_entry"]

    updated_file_entry = file_utils.add_file_from_remote_directory(file_entry, sample_id)

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


add_remote_file_to_sample.methods = ("POST",)  # type: ignore


def delete_file_from_sample():
    """Remove a file from a sample, but don't delete the actual file (for now)"""

    request_json = request.get_json()

    sample_id = request_json["sample_id"]
    file_id = ObjectId(request_json["file_id"])
    print(f"delete_file_from_sample: sample: {sample_id} file: {file_id}")
    print("deleting file from sample")
    result = pydatalab.mongo.flask_mongo.db.data.update_one(
        {"sample_id": sample_id}, {"$pull": {"file_ObjectIds": file_id}}
    )
    if result.modified_count != 1:
        return (
            jsonify(
                status="error",
                message=f"{sample_id} {file_id} delete failed. Something went wrong with the db call to remove file from sample.",
                output=result.raw_result,
            ),
            400,
        )
    print("deleting sample from file")
    updated_file_entry = pydatalab.mongo.flask_mongo.db.files.find_one_and_update(
        {"_id": file_id},
        {"$pull": {"sample_ids": sample_id}},
        return_document=ReturnDocument.AFTER,
    )

    if not updated_file_entry:
        return (
            jsonify(
                status="error",
                message=f"{sample_id} {file_id} delete failed. Something went wrong with the db call to remove sample from file",
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


delete_file_from_sample.methods = ("POST",)  # type: ignore


def delete_file():
    """delete a data file from the uploads/sample_id folder"""

    request_json = request.get_json()

    sample_id = request_json["sample_id"]
    filename = request_json["filename"]

    secure_sample_id = secure_filename(sample_id)
    secure_fname = secure_filename(filename)

    path = os.path.join(CONFIG.FILE_DIRECTORY, secure_sample_id, secure_fname)

    if not os.path.isfile(path):
        return (
            jsonify(
                status="error",
                message="Delete failed. file not found: {}".format(path),
            ),
            400,
        )

    print("Deleting path: {}".format(path))
    result = pydatalab.mongo.flask_mongo.db.data.update_one(
        {"sample_id": sample_id},
        {"$pull": {"files": filename}},
        return_document=ReturnDocument.AFTER,
    )
    if result.matched_count != 1:
        return (
            jsonify(
                status="error",
                message=f"{sample_id} {filename} delete failed. Something went wrong with the db call. File not deleted.",
                output=result.raw_result,
            ),
            400,
        )
    print(f"removing file: {path}")
    # import pdb; pdb.set_trace()
    os.remove(path)

    return jsonify({"status": "success"}), 200


delete_file.methods = ("POST",)  # type: ignore

ENDPOINTS: Dict[str, Callable] = {
    "/files/<string:file_id>/<string:filename>": get_file,
    "/upload-file/": upload,
    "/add-remote-file-to-sample/": add_remote_file_to_sample,
    "/delete-file-from-sample/": delete_file_from_sample,
    "/delete-file/": delete_file,
}
