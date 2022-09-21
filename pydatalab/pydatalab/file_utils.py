import datetime
import os
import re
import shutil
import subprocess
from typing import Any, Dict, Union

from bson.objectid import ObjectId
from pymongo import ReturnDocument
from werkzeug.utils import secure_filename

import pydatalab.mongo
from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER, logged_route
from pydatalab.models import File

FILE_DIRECTORY = CONFIG.FILE_DIRECTORY
DIRECTORIES_DICT = {fs["name"]: fs for fs in CONFIG.REMOTE_FILESYSTEMS}


@logged_route
def _sync_file_with_remote(remote_path: str, src: str) -> None:
    """Copy a file from a mounted volume or ssh-able remote to the
    local file store.

    Arguments:
        remote_path: The original location of the file.
        src: The local location of the file.
    """
    if os.path.isfile(remote_path):
        shutil.copy(remote_path, src)
    elif remote_path.startswith("ssh://"):
        scp_command = f"scp \"{re.sub('^ssh://', '', remote_path)}\" {src}"

        LOGGER.debug("Syncing file with '%s'", scp_command)
        proc = subprocess.Popen(
            scp_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = proc.communicate()
        if stderr:
            raise RuntimeError(
                f"scp command {scp_command} raised the the following errors: {stderr!r}"
            )

    if not os.path.isfile(src):
        raise RuntimeError("Something went wrong copying {remote_path} to {src}.")


@logged_route
def _check_and_sync_file(file_info: File, file_id: ObjectId) -> File:
    """For a given file, check if the remote version is newer
    than the stored version and sync them if so.

    Args:
        file_info: The `File` metadata object.
        file_id: The `bson.ObjectId` of the file stored in the database
            (used to update the file collection).

    Returns:
        The updated file info, if an update was required,
        otherwise the old file info.

    """
    file_collection = pydatalab.mongo.flask_mongo.db.files
    if not file_info.source_server_name or not file_info.source_path:
        raise RuntimeError("Attempted to sync file %s with no known remote", file_info)

    if not file_info.last_modified_remote:
        LOGGER.warning(
            "Unable to sync file %s, no last modified timestamp. Will use saved version.",
            file_info.source_path,
        )
        return file_info

    cached_timestamp = file_info.last_modified_remote
    remote = DIRECTORIES_DICT.get(file_info.source_server_name, None)
    if not remote:
        LOGGER.warning(
            f"Could not find desired remote for {file_info.source_server_name!r}, cannot sync file"
        )
        return file_info

    full_remote_path = os.path.join(remote["path"], file_info.source_path)
    if remote["hostname"]:
        full_remote_path = f'{remote["hostname"]}:{full_remote_path}'

    if full_remote_path.startswith("ssh://"):
        # For ssh-able remotes, check age of the local file, rather than the last time the remote file was modified
        remote_timestamp = datetime.datetime.now()

    else:
        try:
            stat_results = os.stat(full_remote_path)
            remote_timestamp = datetime.datetime.fromtimestamp(stat_results.st_mtime)
        except FileNotFoundError:
            LOGGER.debug(
                "Could not access remote file when checking for latest version: %s",
                full_remote_path,
            )
            return file_info

    # file_info.live_update_error = "Could not reach remote server to update
    if remote_timestamp > cached_timestamp + datetime.timedelta(
        minutes=CONFIG.REMOTE_CACHE_MAX_AGE
    ):
        LOGGER.debug("Updating file %s to latest version", file_info.source_path)

        try:
            _sync_file_with_remote(full_remote_path, file_info.location)
        except RuntimeError:
            LOGGER.warning(
                "Unable to sync file %s with %s on server.", file_info.location, full_remote_path
            )
            return file_info

        if file_info.location is not None:
            new_stat_results = os.stat(file_info.location)

            updated_file_info = file_collection.find_one_and_update(
                {"_id": file_id},
                {
                    "$set": {
                        "size": new_stat_results.st_size,
                        "last_modified": datetime.datetime.fromtimestamp(new_stat_results.st_mtime),
                        "last_modified_remote": remote_timestamp,
                        "version": file_info.version + 1,
                    }
                },
                return_document=ReturnDocument.AFTER,
            )

            return File(**updated_file_info)

    LOGGER.debug("File %s is recent enough, not updating", file_info.source_path)
    return file_info


def get_file_info_by_id(
    file_id: Union[str, ObjectId], update_if_live: bool = True
) -> Dict[str, Any]:
    """Query the files collection for the given ID.

    If the `update_if_live` and the file has been updated on the
    remote since it was added to the database, then the new version
    will be copied into the local filestore.

    Arguments:
        file_id: Either the string or ObjectID representatoin of the file ID.
        update_if_live: Whether or not to update the stored file to a
            newer version, if it exists.

    Raises:
        IOError: If the given file ID does not exist in the database.

    Returns:
        The stored file information as a dictonary. Will be empty if the
            corresponding file does not exist on disk.

    """
    LOGGER.debug("getting file for file_id: %s", file_id)
    file_collection = pydatalab.mongo.flask_mongo.db.files
    file_id = ObjectId(file_id)
    file_info = file_collection.find_one({"_id": file_id})
    if not file_info:
        raise IOError(f"could not find file with id: {file_id} in db")

    file_info = File(**file_info)

    if update_if_live and file_info.is_live:
        file_info = _check_and_sync_file(file_info, file_id)

    return file_info.dict()


def update_uploaded_file(file, file_id, last_modified=None, size_bytes=None):
    """file is a file object from a flask request.
    last_modified should be an isodate format. if None, the current time will be inserted
    By default, only changes the last_modified, and size_bytes, increments version, and verifies source=remote and is_live=false. (converts )
    additional_updates can be used to pass other fields to change in (NOT IMPLEMENTED YET)"""

    last_modified = datetime.datetime.now().isoformat()
    file_collection = pydatalab.mongo.flask_mongo.db.files

    updated_file_entry = file_collection.find_one_and_update(
        {"_id": file_id},  # Note, needs to be ObjectID()
        {
            "$set": {
                "last_modified": last_modified,
                "size": size_bytes,
                "source": "remote",
                "is_live": False,
            },
            "$inc": {"version": 1},
        },
        return_document=ReturnDocument.AFTER,
    )

    if not updated_file_entry:
        raise IOError(f"Issue with db update uploaded file {file.name} id {file_id}")

    updated_file_entry = File(**updated_file_entry)

    # overwrite the old file with the new location
    file.save(updated_file_entry["location"])

    ret = updated_file_entry.dict()
    ret.update({"_id": file_id})
    return ret


def save_uploaded_file(file, item_ids=None, block_ids=None, last_modified=None, size_bytes=None):
    """file is a file object from a flask request.
    last_modified should be an isodate format. if last_modified is None, the current time will be inserted"""
    sample_collection = pydatalab.mongo.flask_mongo.db.items
    file_collection = pydatalab.mongo.flask_mongo.db.files

    # validate item_ids
    if not item_ids:
        item_ids = []
    if not block_ids:
        block_ids = []

    for item_id in item_ids:
        if not sample_collection.find_one({"item_id": item_id}):
            raise ValueError(f"item_id is invalid: {item_id}")

    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)[1]

    if not last_modified:
        last_modified = datetime.datetime.now().isoformat()

    new_file_document = File(
        name=filename,
        original_name=file.filename,  # not escaped
        location=None,  # file storage location in datalab. Important! will be filled in below
        url_path=None,  # the url used to access this file. Important! will be filled in below
        extension=extension,
        source="uploaded",
        size=size_bytes,
        item_ids=item_ids,
        blocks=block_ids,
        last_modified=last_modified,
        time_added=last_modified,
        metadata={},
        representation=None,
        source_server_name=None,  # not used for source=uploaded
        source_path=None,  # not used for source=uploaded
        last_modified_remote=None,  # not used for source=uploaded
        is_live=False,  # not available for source=uploaded
        version=1,  # increment with each update
    )

    result = file_collection.insert_one(new_file_document.dict())
    if not result.acknowledged:
        raise IOError(f"db operation failed when trying to insert new file. Result: {result}")

    inserted_id = result.inserted_id

    new_directory = os.path.join(FILE_DIRECTORY, str(inserted_id))
    file_location = os.path.join(new_directory, filename)
    os.makedirs(new_directory)
    file.save(file_location)

    updated_file_entry = file_collection.find_one_and_update(
        {"_id": inserted_id},
        {
            "$set": {
                "location": file_location,
                "size": os.path.getsize(file_location),
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    updated_file_entry = File(**updated_file_entry)

    # update any referenced item_ids
    for item_id in item_ids:
        sample_update_result = sample_collection.update_one(
            {"item_id": item_id}, {"$push": {"file_ObjectIds": inserted_id}}
        )
        if sample_update_result.modified_count != 1:
            raise IOError(
                f"db operation failed when trying to insert new file ObjectId into sample: {item_id}"
            )

    ret = updated_file_entry.dict()
    ret.update({"_id": inserted_id})
    return ret


def add_file_from_remote_directory(file_entry, item_id, block_ids=None):
    file_collection = pydatalab.mongo.flask_mongo.db.files
    sample_collection = pydatalab.mongo.flask_mongo.db.items

    if not block_ids:
        block_ids = []
    filename = secure_filename(file_entry["name"])
    extension = os.path.splitext(filename)[1]

    # generate the remote url
    host = DIRECTORIES_DICT[file_entry["toplevel_name"]]

    remote_path = os.path.join(file_entry["relative_path"].lstrip("/"), file_entry["name"])

    # If we are dealing with a truly remote host
    if host["hostname"]:
        remote_toplevel_path = f'{host["hostname"]}:{host["path"]}'
        full_remote_path = f"{remote_toplevel_path}/{remote_path}"
        if file_entry.get("time") is None:
            remote_timestamp = None
        else:
            remote_timestamp = datetime.datetime.fromtimestamp(int(file_entry["time"]))

    # Otherwise we assume the file is mounted locally
    else:
        remote_toplevel_path = host["path"]
        full_remote_path = os.path.join(remote_toplevel_path, remote_path)
        # check that the path is valid and get the last modified time from the server
        remote_timestamp = os.path.getmtime(full_remote_path)

    new_file_document = File(
        name=filename,
        original_name=file_entry["name"],  # not escaped
        # file storage location in datalab. Important! will be filled in below
        location=None,
        # the URL used to access this file. Important! will be filled in below
        url_path=None,
        extension=extension,
        source="remote",
        size=file_entry["size"],
        item_ids=[item_id],
        blocks=block_ids,
        # last_modified is the last modified time of the db entry in isoformat. For last modified file timestamp, see last_modified_remote_timestamp
        last_modified=datetime.datetime.now().isoformat(),
        time_added=datetime.datetime.now().isoformat(),
        metadata={},
        representation=None,
        source_server_name=file_entry["toplevel_name"],
        # this is the relative path from the given source_server_name (server directory)
        source_path=remote_path,
        # last modified time as provided from the remote server. May by different than last_modified if the two servers times are not synchrotronized.
        last_modified_remote=remote_timestamp,
        # Whether this file will update (if changes have occured) on access
        is_live=bool(host["hostname"]),
        # incremented with each update
        version=1,
    )

    result = file_collection.insert_one(new_file_document.dict())
    if not result.acknowledged:
        raise IOError(f"db operation failed when trying to insert new file. Result: {result}")

    inserted_id = result.inserted_id

    new_directory = os.path.join(FILE_DIRECTORY, str(inserted_id))
    new_file_location = os.path.join(new_directory, filename)
    os.makedirs(new_directory)
    _sync_file_with_remote(full_remote_path, new_file_location)

    updated_file_entry = file_collection.find_one_and_update(
        {"_id": inserted_id},
        {
            "$set": {
                "location": new_file_location,
                "url_path": new_file_location,
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    sample_update_result = sample_collection.update_one(
        {"item_id": item_id}, {"$push": {"file_ObjectIds": inserted_id}}
    )
    if sample_update_result.modified_count != 1:
        raise IOError(
            f"db operation failed when trying to insert new file ObjectId into sample: {item_id}"
        )

    return updated_file_entry


def retrieve_file_path(file_ObjectId):
    file_collection = pydatalab.mongo.flask_mongo.db.files
    result = file_collection.find_one({"_id": ObjectId(file_ObjectId)})
    if not result:
        raise FileNotFoundError(
            f"The file with file_ObjectId: {file_ObjectId} could not be found in the database"
        )

    result = File(**result)

    return result.location


def remove_file_from_sample(item_id: Union[str, ObjectId], file_id: Union[str, ObjectId]) -> None:
    """Detach the file at `file_id` from the item at `item_id`.

    Args:
        item_id: The database ID of the item to alter.
        file_id: The database ID of the file to remove from the item.

    """
    item_id, file_id = ObjectId(item_id), ObjectId(file_id)
    sample_collection = pydatalab.mongo.flask_mongo.db.items
    file_collection = pydatalab.mongo.flask_mongo.db.files
    sample_result = sample_collection.update_one(
        {"item_id": item_id},
        {"$pull": {"file_ObjectIds": file_id}},
    )

    if sample_result.modified_count < 1:
        raise IOError(
            f"Failed to remove {file_id!r} from item {item_id!r}. Result: {sample_result.raw_result}"
        )

    file_collection.update_one(
        {"_id": file_id},
        {"$pull": {"item_ids": item_id}},
    )
