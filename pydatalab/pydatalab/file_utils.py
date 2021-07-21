import datetime
import os
import shutil

from bson.objectid import ObjectId
from flask import jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename

from resources import DIRECTORIES, DIRECTORIES_DICT

client = MongoClient("mongodb://localhost:27017/")
db = client.datalabvue
FILE_COLLECTION = db.files
SAMPLE_COLLECTION = db.data

FILE_DIRECTORY = "files"


def get_file_info_by_id(file_id, update_if_live=True):
    """file_id can be either the string representation or the ObjectId() object. Returns the file information dictionary"""
    print(f"getting file for file_id: {file_id}")
    file_id = ObjectId(file_id)
    file_info = FILE_COLLECTION.find_one({"_id": file_id})
    if not file_info:
        raise IOError(f"could not find file with id: {file_id} in db")

    if update_if_live and file_info["is_live"]:
        remote_toplevel_path = DIRECTORIES_DICT[file_info["source_server_name"]]["path"]
        full_remote_path = os.path.join(remote_toplevel_path, file_info["source_path"])
        cached_timestamp = file_info["last_modified_remote_timestamp"]
        try:
            stat_results = os.stat(full_remote_path)
        except FileNotFoundError as e:
            print(
                "when trying to check if live file needs to be updated, could not access remote file"
            )
            file_info["live_update_error"] = "Could not reach remote server to update"
            return file_info

        current_timestamp_on_server = stat_results.st_mtime
        print(
            f"checking if update is necessary. Cached timestamp: {cached_timestamp}. Current timestamp: {current_timestamp_on_server}."
        )
        print(f"\tDifference: {current_timestamp_on_server - cached_timestamp} seconds")
        if current_timestamp_on_server > cached_timestamp:
            print("updating file")
            shutil.copy(full_remote_path, file_info["location"])
            updated_file_info = FILE_COLLECTION.find_one_and_update(
                {"_id": file_info["_id"]},
                {
                    "$set": {
                        "size": stat_results.st_size,
                        "last_modified": datetime.datetime.now().isoformat(),
                        "last_modified_remote_timestamp": current_timestamp_on_server,
                        "version": file_info["version"] + 1,
                    }
                },
            )

            return updated_file_info
    return file_info


def update_uploaded_file(file, file_id, last_modified=None, size_bytes=None, **additional_updates):
    """file is a file object from a flask request.
    last_modified should be an isodate format. if None, the current time will be inserted
    By default, only changes the last_modified, and size_bytes, increments version, and verifies source=remote and is_live=false. (converts )
    additional_updates can be used to pass other fields to change in (NOT IMPLEMENTED YET)"""

    last_modified = datetime.datetime.now().isoformat()

    updated_file_entry = FILE_COLLECTION.find_one_and_update(
        {"_id": file_id},  # Note, needs to be ObjectID()
        {
            "$set": {
                "last_modified": last_modified,
                "size_bytes": size_bytes,
                "source": "remote",
                "is_live": False,
            },
            "$inc": {"version": 1},
        },
    )

    if not updated_file_entry:
        import pdb

        pdb.set_trace()
        raise IOError(f"Issue with db update uploaded file {file.name} id {file_id}")

    # overwrite the old file with the new location
    file.save(updated_file_entry["location"])

    return updated_file_entry


def save_uploaded_file(file, sample_ids=[], block_ids=[], last_modified=None, size_bytes=None):
    """file is a file object from a flask request.
    last_modified should be an isodate format. if last_modified is None, the current time will be inserted"""

    # validate sample_ids
    for sample_id in sample_ids:
        if not SAMPLE_COLLECTION.find_one({"sample_id": sample_id}):
            raise ValueError(f"sample_id is invalid: {sample_id}")

    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)[1]

    if not last_modified:
        last_modified = datetime.datetime.now().isoformat()

    new_file_document = {
        "name": filename,
        "original_name": file.filename,  # not escaped
        "location": None,  # file storage location in datalab. Important! will be filled in below
        "url_path": None,  # the url used to access this file. Important! will be filled in below
        "extension": extension,
        "source": "uploaded",
        "size": size_bytes,
        "sample_ids": sample_ids,
        "blocks": block_ids,
        "last_modified": last_modified,
        "time_added": last_modified,
        "metadata": {},
        "representation": None,
        "source_server_name": None,  # not used for source=uploaded
        "source_path": None,  # not used for source=uploaded
        "last_modified_remote": None,  # not used for source=uploaded
        "is_live": False,  # not available for source=uploaded
        "version": 1,  # increment with each update
    }

    result = FILE_COLLECTION.insert_one(new_file_document)
    if not result.acknowledged:
        raise IOError(f"db operation failed when trying to insert new file. Result: {result}")

    inserted_id = result.inserted_id

    new_directory = os.path.join(FILE_DIRECTORY, str(inserted_id))
    file_location = os.path.join(new_directory, filename)
    os.makedirs(new_directory)
    file.save(file_location)

    updated_file_entry = FILE_COLLECTION.find_one_and_update(
        {"_id": inserted_id},
        {
            "$set": {
                "location": file_location,
                "url_path": file_location,
            }
        },
    )

    # update any referenced sample_ids
    for sample_id in sample_ids:
        sample_update_result = SAMPLE_COLLECTION.update_one(
            {"sample_id": sample_id}, {"$push": {"file_ObjectIds": inserted_id}}
        )
        if sample_update_result.modified_count != 1:
            raise IOError(
                f"db operation failed when trying to insert new file ObjectId into sample: {sample_id}"
            )

    return updated_file_entry


def add_file_from_remote_directory(file_entry, sample_id, block_ids=[]):
    filename = secure_filename(file_entry["name"])
    extension = os.path.splitext(filename)[1]

    # generate the remote url
    remote_toplevel_path = DIRECTORIES_DICT[file_entry["toplevel_name"]]["path"]
    remote_path = os.path.join(file_entry["relative_path"].lstrip("/"), file_entry["name"])
    full_remote_path = os.path.join(remote_toplevel_path, remote_path)

    # check that the path is valid and get the last modified time from the server
    last_modified_timestamp_from_remote = os.path.getmtime(full_remote_path)

    new_file_document = {
        "name": filename,
        "original_name": file_entry["name"],  # not escaped
        "location": None,  # file storage location in datalab. Important! will be filled in below
        "url_path": None,  # the url used to access this file. Important! will be filled in below
        "extension": extension,
        "source": "remote",
        "size": file_entry["size"],  # not actually in bytes at the moment. in human-readable format
        "sample_ids": [sample_id],
        "blocks": block_ids,
        "last_modified": datetime.datetime.now().isoformat(),  # last_modified is the last modified time of the db entry in isoformat. For last modified file timestamp, see last_modified_remote_timestamp
        "time_added": datetime.datetime.now().isoformat(),
        "metadata": {},
        "representation": None,
        "source_server_name": file_entry["toplevel_name"],
        "source_path": remote_path,  # this is the relative path from the given source_server_name (server directory)
        "last_modified_remote_timestamp": last_modified_timestamp_from_remote,  # last modified time as provided from the remote server. May by different than last_modified if the two servers times are not synchrotronized.
        "is_live": True,  # will update (if changes have occured) on access
        "version": 1,  # increment with each update
    }

    result = FILE_COLLECTION.insert_one(new_file_document)
    if not result.acknowledged:
        raise IOError(f"db operation failed when trying to insert new file. Result: {result}")

    inserted_id = result.inserted_id

    new_directory = os.path.join(FILE_DIRECTORY, str(inserted_id))
    new_file_location = os.path.join(new_directory, filename)
    os.makedirs(new_directory)
    remote_file_path = shutil.copy(full_remote_path, new_file_location)

    updated_file_entry = FILE_COLLECTION.find_one_and_update(
        {"_id": inserted_id},
        {
            "$set": {
                "location": new_file_location,
                "url_path": new_file_location,
            }
        },
    )

    sample_update_result = SAMPLE_COLLECTION.update_one(
        {"sample_id": sample_id}, {"$push": {"file_ObjectIds": inserted_id}}
    )
    if sample_update_result.modified_count != 1:
        raise IOError(
            f"db operation failed when trying to insert new file ObjectId into sample: {sample_id}"
        )

    return updated_file_entry


def retrieve_file_path(file_ObjectId):
    result = FILE_COLLECTION.find_one({"_id": ObjectId(file_ObjectId)})
    if not result:
        raise (
            FileNotFoundError,
            f"The file with file_ObjectId: {file_ObjectId} could not be found in the database",
        )
    return result["location"]


def remove_file_from_sample(sample_id, file_ObjectId):
    sample_result = SAMPLE_COLLECTION.update_one(
        {"sample_id": ObjectId(file_id)},
        {"$pull": {"file_ObjectIds": ObjectId(file_ObjectId)}},
    )

    if sample_result.modified_count < 1:
        raise (
            IOError,
            f"failed to remove file_ObjectId (f{file_ObjectId}) from sample (f{sample_id}) db entry: {sample_result.raw_result}",
        )

    file_result = FILE_COLLECTION.update_one(
        {"_id": ObjectId(file_ObjectId)},
        {"$pull": {"sample_ids": ObjectId(file_ObjectId)}},
    )


# def add_file_to_db(file, source, is_live=False, source_server_name=None,source_path=None, sample_ids=[], block_ids=[], size_bytes=None):
#    ''' file is a python file object. source should be either "uploaded" or "remote", signifying either a
#    local upload from the user, or remote server (one of the servers specified in remote_filesystems.py)'''
#    assert source in ["uploaded", "remote"], f'source: "{source}" is invalid. Must be either "uploaded" or "remote"'

#    # if the file comes from a remote server, must provide the name of the server and the path on the server
#    if source == "remote":
#       assert source_server_name is not None, 'for "remote" source, source_server_name must be provided'
#       assert source_path is not None, 'for "remote" source, source_path must be provided'

#    if source != "remote":
#       assert not is_live, 'live mode can only be used with "remote" source.'

#    filename = file.name
#    extension = os.path.splitext(filename)[1]

#    new_file_document = {
#       "name": filename,
#       "location": None, # the location where the file is stored. Important! Will be filled in below
#       "extension": extension,
#       "source": source,
#       "source_path": source_path,
#       "size": size_bytes,
#       "representation": None, # could be used to store the data
#       "samples": sample_ids,# sample_ids of any samples this file is included in.
#       "blocks": block_ids, # block_ids of any blocks this file is included in
#       "metadata": {}, # to store metadata collected from the file
#       "type": None, # file type
#       "is_live": bool(is_live) # if true, this file will be updated as it is updated on the remote server.
#    }

#    result = file_collection.insert_one(new_file_document)
#    if not result.acknowledged:
#       raise IOError(f"db operation failed when trying to insert new file. Result: {result}")

#    inserted_id = result.inserted_id

#    file_save_location = os.path.join(FILE_DIRECTORY, str(inserted_id), filename)
#    file.write()


#    return result
#    print("added")


# def save_file_to ():


# # def delete_file(file_uid):
