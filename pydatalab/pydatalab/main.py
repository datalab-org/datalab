import datetime
import os
import pprint
from typing import Any, Dict

from bson import ObjectId, json_util
from flask import Flask, abort, jsonify, request, send_from_directory
from flask.json import JSONEncoder
from flask_cors import CORS
from pymongo import ReturnDocument
from werkzeug.utils import secure_filename

import pydatalab.mongo
from pydatalab import file_utils, remote_filesystems
from pydatalab.blocks import BLOCK_KINDS

CONFIG = {
    "SECRET_KEY": "dummy key dont use in production",
    "MONGO_URI": "mongodb://localhost:27017/datalabvue",
    "UPLOAD_PATH": "uploads",
    "FILE_DIRECTORY": "files",
}


# use a json encoder that can handle pymongo's bson
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        return json_util.default(obj)


def create_app(config_override: Dict[str, Any] = None) -> Flask:
    """Create the `Flask` app with the given config.

    Parameters:
        config_override: Config value overrides to use
            within the `Flask` app.

    Returns:
        The `Flask` app with all associated endpoints.

    """

    app = Flask(__name__, instance_relative_config=True)

    if config_override:
        CONFIG.update(config_override)

    app.config.update(CONFIG)
    CORS(app, resources={r"/*": {"origins": "*"}})

    app.json_encoder = CustomJSONEncoder

    # Must use the full path so that this object can be mocked for testing
    flask_mongo = pydatalab.mongo.flask_mongo
    flask_mongo.init_app(app)

    DATA_COLLECTION = flask_mongo.db.data
    FILE_COLLECTION = flask_mongo.db.files
    FILESYSTEMS_COLLECTION = flask_mongo.db.remoteFilesystems

    @app.route("/")
    def index():
        return "Hello, This is a server"

    @app.route("/samples/", methods=["GET"])
    def get_sample_list():
        cursor = DATA_COLLECTION.aggregate(
            [
                {
                    "$project": {
                        "_id": 0,
                        "sample_id": 1,
                        "nblocks": {"$size": "$display_order"},
                        "date": 1,
                        "chemform": 1,
                        "name": 1,
                    }
                }
            ]
        )
        return jsonify({"status": "success", "samples": list(cursor)})

    @app.route("/new-sample/", methods=["POST"])
    def create_new_sample():
        request_json = request.get_json()
        print(f"creating new samples with: {request_json}")
        sample_id = request_json["sample_id"]
        name = request_json["name"]
        date = request_json["date"]

        # check to make sure that sample_id isn't taken already
        print("Validating sample id...")
        if DATA_COLLECTION.find_one({"sample_id": sample_id}):
            print(f"Sample ID '{sample_id}' already exists in database")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "sample_id_validation_error",
                    }
                ),
                400,
            )
        print("Sample ID is unique, and can be added to the database")

        new_sample = {
            "sample_id": sample_id,
            "name": name,
            "date": date,
            "description": "",
            "blocks": [],  # an array of subdocuments
            "blocks_obj": {},
            "files": [],
            "file_ObjectIds": [],
            "display_order": [],  # an array of strings, which are ids for the blocks
        }

        result = DATA_COLLECTION.insert_one(new_sample)
        if not result.acknowledged:
            return (
                jsonify(
                    status="error",
                    message=f"Failed to add new block to server.",
                    output=result.raw_result,
                ),
                400,
            )
        print("sample has been added to the database")
        return (
            jsonify(
                {
                    "status": "success",
                    "sample_list_entry": {
                        "sample_id": sample_id,
                        "nblocks": 0,
                        "date": date,
                        "name": name,
                    },
                }
            ),
            200,
        )

    @app.route("/delete-sample/", methods=["POST"])
    def delete_sample():
        request_json = request.get_json()
        sample_id = request_json["sample_id"]
        print(f"received request to delete sample {sample_id}")

        result = DATA_COLLECTION.delete_one({"sample_id": sample_id})

        if result.deleted_count != 1:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Failed to delete sample from database",
                    }
                ),
                400,
            )
        print("Deleted successfully!")
        return (
            jsonify(
                {
                    "status": "success",
                }
            ),
            200,
        )

    @app.route("/get_sample_data/<sample_id>", methods=["GET"])
    def get_sample_data(sample_id):
        # retrieve the entry from the databse:
        doc = DATA_COLLECTION.find_one(
            {"sample_id": sample_id},
        )
        if not doc:
            abort(404)
        # form = NewSampleForm(data=doc)
        # last_modified = doc["last_modified"] if "last_modified" in doc else None

        # pass all blocks through their Block objects to add any properties needed
        for block_id, block_data in doc["blocks_obj"].items():
            block_type = block_data["blocktype"]

            # temporary fix to not crash server for not implemented blocks.
            if block_type not in BLOCK_KINDS:
                doc["blocks_obj"][block_id] = block_data
            else:
                Block = BLOCK_KINDS[block_type].from_db(block_data)
                doc["blocks_obj"][block_id] = Block.to_web()

        files_data = {}
        if doc["file_ObjectIds"]:
            files_cursor = FILE_COLLECTION.find({"_id": {"$in": doc["file_ObjectIds"]}})

            for f in files_cursor:
                files_data[str(f["_id"])] = f
        pprint.pprint(files_data)

        doc["file_ObjectIds"] = [
            str(x) for x in doc["file_ObjectIds"]
        ]  # send string ids, not ObjectId()

        return jsonify(
            {
                "status": "success",
                "sample_id": sample_id,
                "sample_data": doc,
                "files_data": files_data,
            }
        )

    def get_files(file_ObjectIds):
        pass

    @app.route("/save-sample/", methods=["POST"])
    def save_sample():
        request_json = request.get_json()
        sample_id = request_json["sample_id"]
        updated_data = request_json["data"]

        strip_keys = ("_id", "file_ObjectIds")

        for k in strip_keys:
            if k in updated_data:
                del updated_data[k]

        updated_data["last_modified"] = datetime.datetime.now().isoformat()

        for block_id, block_data in updated_data.get("blocks_obj", {}).items():
            blocktype = block_data["blocktype"]
            Block = BLOCK_KINDS[blocktype].from_web(block_data)
            updated_data["blocks_obj"][block_id] = Block.to_db()

        print("save-sample received request\n\tsample:{}\ndata:{}".format(sample_id, updated_data))

        result = DATA_COLLECTION.update_one({"sample_id": sample_id}, {"$set": updated_data})

        print(result.raw_result)
        if result.matched_count != 1:
            return (
                jsonify(
                    status="error",
                    message=f"{blocktype} Update failed. no subdocument matched",
                    output=result.raw_result,
                ),
                400,
            )

        return jsonify(status="success")

    # Custom static route for the datafiles
    # @app.route('/files/<sample_id>/<path:filename>')
    # def get_file(sample_id, filename):
    # 	path = os.path.join(app.config['UPLOAD_PATH'], sample_id)
    # 	print("retrieving file: {} from {}".format(filename, path))
    # 	return send_from_directory(path, filename)
    @app.route("/files/<string:file_id>/<string:filename>")
    def get_file(file_id, filename):
        path = os.path.join(app.config["FILE_DIRECTORY"], file_id)

        print("retrieving file: {} from {}".format(filename, path))
        return send_from_directory(path, filename)

    @app.route("/upload-file/", methods=["POST"])
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

    @app.route("/add-remote-file-to-sample/", methods=["POST"])
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

    @app.route("/delete-file-from-sample/", methods=["POST"])
    def delete_file_from_sample():
        """Remove a file from a sample, but don't delete the actual file (for now)"""

        request_json = request.get_json()

        sample_id = request_json["sample_id"]
        file_id = ObjectId(request_json["file_id"])
        print(f"delete_file_from_sample: sample: {sample_id} file: {file_id}")
        print("deleting file from sample")
        result = DATA_COLLECTION.update_one(
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
        updated_file_entry = FILE_COLLECTION.find_one_and_update(
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

    @app.route("/delete-file/", methods=["POST"])
    def delete_file():
        """delete a data file from the uploads/sample_id folder"""

        request_json = request.get_json()

        sample_id = request_json["sample_id"]
        filename = request_json["filename"]

        secure_sample_id = secure_filename(sample_id)
        secure_fname = secure_filename(filename)

        path = os.path.join(app.config["UPLOAD_PATH"], secure_sample_id, secure_fname)

        if not os.path.isfile(path):
            return (
                jsonify(
                    status="error",
                    message="Delete failed. file not found: {}".format(path),
                ),
                400,
            )

        print("Deleting path: {}".format(path))
        result = DATA_COLLECTION.update_one(
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

    # TODO: add input data validation
    @app.route("/add-data-block/", methods=["POST"])
    def add_data_block():
        """Call with AJAX to add a block to the sample"""

        request_json = request.get_json()

        # pull out required arguments from json
        sample_id = request_json["sample_id"]
        block_type = request_json["block_kind"]
        insert_index = request_json["index"]

        print(f"Adding a block of type: {block_type} to sample: {sample_id}")
        if block_type not in BLOCK_KINDS:
            return jsonify(status="error", message="Invalid block type"), 400

        block = BLOCK_KINDS[block_type](sample_id=sample_id)

        data = block.to_db()
        # print("updating the database with:")
        # print(sample_id)
        # print(data)
        # print(insert_index)

        # currently, adding to both blocks and blocks_obj to mantain compatibility with
        # the old site. The new site only uses blocks_obj
        if insert_index:
            display_order_update = {
                "$each": [block.block_id],
                "$position": insert_index,
            }
        else:
            display_order_update = block.block_id

        result = DATA_COLLECTION.update_one(
            {"sample_id": sample_id},
            {
                "$push": {"blocks": data},
                "$set": {f"blocks_obj.{block.block_id}": data},
                "$push": {"display_order": display_order_update},
            },
        )

        print(result.raw_result)
        if result.modified_count < 1:
            return (
                jsonify(
                    status="error",
                    message="Update failed. The sample_id probably incorrect: {}".format(sample_id),
                ),
                400,
            )

        # get the new display_order:
        display_order_result = DATA_COLLECTION.find_one(
            {"sample_id": sample_id}, {"display_order": 1}
        )
        print("new document: {}".format(display_order_result))

        return jsonify(
            status="success",
            new_block_obj=block.to_web(),
            new_display_order=display_order_result["display_order"],
        )

    @app.route("/update-block/", methods=["POST"])
    def update_block():
        """Take in json block data from site, process, and spit
        out updated data. May be used, for example, when the user
        changes plot parameters and the server needs to generate a new
        plot
        """
        request_json = request.get_json()
        print("update_block called with : " + str(request_json)[:1000])
        sample_id = request_json["sample_id"]
        block_id = request_json["block_id"]
        block_data = request_json["block_data"]
        blocktype = block_data["blocktype"]

        Block = BLOCK_KINDS[blocktype].from_web(block_data)

        return jsonify(status="success", new_block_data=Block.to_web()), 200

    @app.route("/delete-block/", methods=["POST"])
    def delete_block():
        """Completely delete a data block fron the database. In the future,
        we may consider preserving data by moving it to a different array,
        or simply making it invisible"""
        request_json = request.get_json()
        sample_id = request_json["sample_id"]
        block_id = request_json["block_id"]

        # print(update)
        result = DATA_COLLECTION.update_one(
            {"sample_id": sample_id},
            {
                "$pull": {
                    "blocks": {"block_id": block_id},
                    "display_order": block_id,
                },
                "$unset": {f"blocks_obj.{block_id}": ""},
            },
        )

        print("Removing block: {} , from sample: {}".format(block_id, sample_id))
        print("result:")
        print(result.raw_result)

        if result.modified_count < 1:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Update failed. The sample_id probably incorrect: {}".format(
                            sample_id
                        ),
                    }
                ),
                400,
            )
        return (
            jsonify({"status": "success"}),
            200,
        )  # could try to switch to http 204 is "No Content" success with no json

    @app.route("/list-remote-directories/", methods=["GET"])
    def list_remote_directories():
        # all_directory_structures = remote_filesystems.get_all_directory_structures()
        all_directory_structures = remote_filesystems.get_all_directory_structures()
        return jsonify(all_directory_structures), 200

    @app.route("/list-remote-directories-cached/")
    def list_remote_directories_cached():
        """return the most recent cached remote directory tree, without actually tree-ing the remote directory"""
        all_directory_structures = remote_filesystems.get_cached_directory_structures()
        last_update_datetimes = [
            datetime.datetime.fromisoformat(d["last_updated"])
            for d in all_directory_structures
            if d["last_updated"]
        ]
        if len(last_update_datetimes):
            print("Last updates from caches:")
            print(last_update_datetimes)
            seconds_since_last_update = (
                datetime.datetime.now() - min(last_update_datetimes)
            ).total_seconds()

        return (
            jsonify(
                {
                    "cached_dir_structures": all_directory_structures,
                    "seconds_since_last_update": seconds_since_last_update,
                    "ncached_not_found": len(all_directory_structures) - len(last_update_datetimes),
                }
            ),
            200,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True, port=5001)
