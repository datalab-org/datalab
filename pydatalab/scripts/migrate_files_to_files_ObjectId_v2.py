#!/usr/bin/env python

import datetime
import os
import shutil

from pymongo import MongoClient, uri_parser
from werkzeug.utils import secure_filename

from pydatalab.config import CONFIG

client = MongoClient(uri_parser.parse_host(CONFIG.MONGO_URI))
database = uri_parser.parse_uri(CONFIG.MONGO_URI).get("database")

if database is None:
    raise RuntimeError("Please specify the MongoDB database as part of the MONGO_URI option.")

db = client[database]
data_collection = db.data
file_collection = db.files

# get all the data
# all_samples = list(data_collection.find({}))
all_samples = [data_collection.find_one({"sample_id": "jdb11-3_e1_s5"})]

for sample in all_samples:
    sample_id = sample["sample_id"]
    print(f"processing: {sample_id}")
    print("existing files: {}".format(sample["files"]))
    secure_sample_id = secure_filename(sample_id)
    original_files_path = os.path.join(CONFIG.FILE_DIRECTORY, secure_sample_id)

    filenames: list[str] = []
    # paths = []
    print(f"{sample_id}:")

    for filename in sample["files"]:
        extension = os.path.splitext(filename)[1]
        old_file_location = os.path.join(
            CONFIG.FILE_DIRECTORY, sample_id, secure_filename(filename)
        )
        if not os.path.isfile(old_file_location):
            print(f"file not found: {old_file_location}")
            continue
        new_file_document = {
            "name": secure_filename(filename),
            "original_name": filename,  # not escaped
            "location": None,  # file storage location in datalab. Important! will be filled in below
            "url_path": None,  # the url used to access this file. Important! will be filled in below
            "extension": extension,
            "source": "uploaded",
            "size": None,
            "sample_ids": [sample_id],
            "blocks": [],
            "last_modified": datetime.datetime.now().isoformat(),  # noqa
            "metadata": {},
            "representation": None,
            "source_server_name": None,  # not used for source=uploaded
            "source_path": None,  # not used for source=uploaded
            "last_modified_remote": None,  # not used for source=uploaded
            "is_live": False,  # not available for source=uploaded
            "version": 1,
        }

        result = file_collection.insert_one(new_file_document)
        if not result.acknowledged:
            raise OSError(f"db operation failed when trying to insert new file. Result: {result}")

        inserted_id = result.inserted_id

        new_directory = os.path.join(CONFIG.FILE_DIRECTORY, str(inserted_id))
        new_file_location = os.path.join(new_directory, filename)
        os.makedirs(new_directory)
        shutil.copy(old_file_location, new_file_location)

        updated_file_entry = file_collection.find_one_and_update(
            {"_id": inserted_id},
            {
                "$set": {
                    "location": new_file_location,
                    "url_path": new_file_location,
                }
            },
        )

        # update the sample entry with the file id
        sample_update_result = data_collection.update_one(
            {"sample_id": sample_id}, {"$push": {"file_ObjectIds": inserted_id}}
        )
        if sample_update_result.modified_count != 1:
            raise OSError(
                f"mdb operation failed when trying to insert new file ObjectId into sample: {sample_id}"
            )
