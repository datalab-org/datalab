import datetime
import os
import pathlib
import re
import shutil
import subprocess
from typing import Any, Dict, Union

from bson.objectid import ObjectId
from pymongo import ReturnDocument
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from pydatalab.config import CONFIG, RemoteFilesystem
from pydatalab.logger import LOGGER, logged_route
from pydatalab.models import File
from pydatalab.models.utils import PyObjectId
from pydatalab.mongo import _get_active_mongo_client, flask_mongo
from pydatalab.permissions import get_default_permissions

LIVE_FILE_CUTOFF = datetime.timedelta(days=31)


def get_space_available_bytes() -> int:
    """For the configured file location, return the number of available bytes, as
    ascertained from the filesystem blocksize and available block count (via Unix-specific
    statvfs system call).

    """
    try:
        stats = os.statvfs(CONFIG.FILE_DIRECTORY)
    except FileNotFoundError:
        raise RuntimeError(f"{CONFIG.FILE_DIRECTORY=} was not safely initialised.")

    return stats.f_bsize * stats.f_bavail


def _escape_spaces_scp_path(remote_path: str) -> str:
    r"""Takes a remote path prefixed by 'ssh://' and encloses
    the filename in quotes and escapes spaces to allow for
    scp'ing of files with spaces in the name, e.g., "ssh://hostname:/path to file"
    becomes 'ssh://hostname:"/path\ to\ file"'.

    Leaves paths without spaces unaltered.

    """
    protocol, host, path = remote_path.split(":")
    if " " not in path:
        return remote_path

    # Escape all spaces, but make sure not to double-escape
    path = path.replace(r"\ ", " ").replace(" ", r"\ ")

    return f'{protocol}:{host}:"{path}"'


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
        # Unescape spaces are we are now quoting the whole path
        remote_path = _escape_spaces_scp_path(remote_path)
        scp_command = f"scp {re.sub('^ssh://', '', remote_path)} {src}"

        pathlib.Path(src).parent.mkdir(parents=False, exist_ok=True)

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
def _call_remote_stat(path: str):
    """Call `stat` on a remote file.

    Args:
        path: The full remote path.

    Returns:
        A dictionary of the `tree` output.

    """

    path = path.strip("ssh://")
    path = path.replace(r"\ ", " ").replace(" ", r"\ ")
    hostname, file_path = path.split(":", 1)
    command = f"ssh {hostname} 'stat -c %Y {file_path}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    LOGGER.debug(f"Calling {command}")
    try:
        stdout, stderr = process.communicate(timeout=20)
        timestamp = int(stdout.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Remote stat process {command!r} returned: {exc!r}")
    if stderr:
        raise RuntimeError(f"Remote statprocess {command!r} returned: {stderr!r}")

    return datetime.datetime.fromtimestamp(timestamp)


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
    directories_dict = {fs.name: fs for fs in CONFIG.REMOTE_FILESYSTEMS}
    file_collection = flask_mongo.db.files
    if not file_info.source_server_name or not file_info.source_path:
        raise RuntimeError("Attempted to sync file %s with no known remote", file_info)

    if not file_info.last_modified_remote:
        LOGGER.warning(
            "Unable to sync file %s, no last modified timestamp. Will use saved version.",
            file_info.source_path,
        )
        return file_info

    cached_timestamp = file_info.last_modified_remote
    remote: RemoteFilesystem | None = directories_dict.get(file_info.source_server_name, None)
    if not remote:
        LOGGER.warning(
            f"Could not find desired remote for {file_info.source_server_name!r} in {directories_dict}, cannot sync file"
        )
        return file_info

    full_remote_path = os.path.join(remote.path, file_info.source_path)
    if remote.hostname:
        full_remote_path = f"{remote.hostname}:{full_remote_path}"

    if full_remote_path.startswith("ssh://"):
        # For ssh-able remotes, check age of the local file, rather than the last time the remote file was modified
        remote_timestamp = _call_remote_stat(full_remote_path)
        LOGGER.debug(
            "File %s was last edited at timestamp %s, %s ago",
            full_remote_path,
            remote_timestamp,
            datetime.datetime.today() - remote_timestamp,
        )

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

    else:
        LOGGER.debug("File %s is recent enough, not updating", file_info.source_path)

    if file_info.location is not None:
        local_stat_results = os.stat(file_info.location)

        # If the file has not been updated in the last cutoff period, do not redownload on every access
        is_live = True
        if datetime.datetime.now() - remote_timestamp > LIVE_FILE_CUTOFF:
            is_live = False

        updated_file_info = file_collection.find_one_and_update(
            {"_id": file_id, **get_default_permissions(user_only=False)},
            {
                "$set": {
                    "size": local_stat_results.st_size,
                    "last_modified": datetime.datetime.fromtimestamp(local_stat_results.st_mtime),
                    "last_modified_remote": remote_timestamp,
                    "is_live": is_live,
                },
                "$inc": {"revision": 1},
            },
            return_document=ReturnDocument.AFTER,
        )

        if updated_file_info is None:
            LOGGER.debug(
                "No updates performed on %s, returned %s",
                file_info.source_path,
                updated_file_info,
            )
            return file_info

        return File(**updated_file_info)

    return file_info


@logged_route
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
    file_collection = flask_mongo.db.files
    file_id = ObjectId(file_id)
    file_info = file_collection.find_one(
        {"_id": file_id, **get_default_permissions(user_only=False)}
    )
    if not file_info:
        raise OSError(f"could not find file with id: {file_id} in db")

    file_info = File(**file_info)

    if update_if_live and file_info.is_live:
        file_info = _check_and_sync_file(file_info, file_id)

    return file_info.dict()


@logged_route
def update_uploaded_file(file, file_id, last_modified=None, size_bytes=None):
    """file is a file object from a flask request.
    last_modified should be an isodate format. if None, the current time will be inserted
    By default, only changes the last_modified, and size_bytes, increments version, and verifies source=remote and is_live=false. (converts )
    additional_updates can be used to pass other fields to change in (NOT IMPLEMENTED YET)"""

    last_modified = datetime.datetime.now().isoformat()
    file_collection = flask_mongo.db.files

    updated_file_entry = file_collection.find_one_and_update(
        {"_id": file_id},  # Note, needs to be ObjectID()
        {
            "$set": {
                "last_modified": last_modified,
                "size": size_bytes,
                "source": "remote",
                "is_live": False,
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )

    if not updated_file_entry:
        raise OSError(f"Issue with db update uploaded file {file.name} id {file_id}")

    updated_file_entry = File(**updated_file_entry)

    # overwrite the old file with the new location
    file.save(updated_file_entry.location)

    ret = updated_file_entry.dict()
    ret.update({"_id": file_id})
    return ret


@logged_route
def save_uploaded_file(
    file: FileStorage,
    item_ids: list[str] | None = None,
    block_ids: list[str] | None = None,
    last_modified: datetime.datetime | str | None = None,
    size_bytes: int | None = None,
    creator_ids: list[PyObjectId | str] | None = None,
) -> dict:
    """Attempt to save a copy of the file object from the request in the file store, and
    add its metadata to the database.

    Parameters:
        file: The flask file object in the request.
        item_ids: The item IDs to attempt to attach the file to.
        block_ids: The block IDs to attempt to attach the file to.
        last_modified: An isoformat datetime for to track as the last time the filed was modified
            (otherwise use the current datetime).
        size_bytes: A hint for the file size in bytes, will be used to verify ahead of time whether
            the file can be saved.
        creator_ids: A list of IDs for users who will be registered as the creator of this file,
            i.e., retaining write access.

    Returns:
        A dictionary containing the saved metadata for the file.

    """

    from pydatalab.permissions import get_default_permissions

    # validate item_ids
    if not item_ids:
        item_ids = []
    if not block_ids:
        block_ids = []

    for item_id in item_ids:
        if not flask_mongo.db.items.find_one(
            {"item_id": item_id, **get_default_permissions(user_only=True)}
        ):
            raise ValueError(f"item_id is invalid: {item_id}")

    if file.filename is None:
        raise RuntimeError("Filename is missing.")

    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)[1]

    if isinstance(last_modified, datetime.datetime):
        last_modified = last_modified.isoformat()

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
        revision=1,  # increment with each update
        creator_ids=creator_ids if creator_ids is not None else [],
    )

    # In one transaction, check if we can save the file, insert it into the database
    # and save it, then release the lock
    client = _get_active_mongo_client()
    with client.start_session(causal_consistency=True) as session:
        space = get_space_available_bytes()
        if size_bytes is not None and space < size_bytes:
            raise RuntimeError(
                f"Cannot store file: insufficient space available on disk (required: {size_bytes // 1024 ** 3} GB). Please contact your datalab administrator."
            )
        file_collection = client.get_database().files
        result = file_collection.insert_one(new_file_document.dict(), session=session)
        if not result.acknowledged:
            raise RuntimeError(
                f"db operation failed when trying to insert new file. Result: {result}"
            )

        inserted_id = result.inserted_id

        new_directory = os.path.join(CONFIG.FILE_DIRECTORY, str(inserted_id))
        file_location = os.path.join(new_directory, filename)
        pathlib.Path(new_directory).mkdir(exist_ok=False)
        file.save(file_location)

    updated_file_entry = flask_mongo.db.files.find_one_and_update(
        {"_id": inserted_id, **get_default_permissions(user_only=False)},
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
        sample_update_result = flask_mongo.db.items.update_one(
            {"item_id": item_id, **get_default_permissions(user_only=True)},
            {"$push": {"file_ObjectIds": inserted_id}},
        )
        if sample_update_result.modified_count != 1:
            raise OSError(
                f"db operation failed when trying to insert new file ObjectId into sample: {item_id}"
            )

    ret = updated_file_entry.dict()
    ret.update({"_id": inserted_id})
    return ret


def add_file_from_remote_directory(
    file_entry, item_id, block_ids=None, creator_ids: list[PyObjectId | str] | None = None
):
    from pydatalab.permissions import get_default_permissions

    file_collection = flask_mongo.db.files
    sample_collection = flask_mongo.db.items
    directories_dict = {fs.name: fs for fs in CONFIG.REMOTE_FILESYSTEMS}

    if not block_ids:
        block_ids = []
    filename = secure_filename(file_entry["name"])
    extension = os.path.splitext(filename)[1]

    # generate the remote url
    host: RemoteFilesystem = directories_dict[file_entry["toplevel_name"]]

    remote_path = os.path.join(file_entry["relative_path"].lstrip("/"), file_entry["name"])

    # If we are dealing with a truly remote host
    remote_timestamp: datetime.datetime | None = None
    if host.hostname:
        remote_toplevel_path = f"{host.hostname}:{host.path}"
        full_remote_path = f"{remote_toplevel_path}/{remote_path}"
        if file_entry.get("time") is not None:
            remote_timestamp = datetime.datetime.fromtimestamp(int(file_entry["time"]))

    # Otherwise we assume the file is mounted locally
    else:
        remote_toplevel_path = str(host.path)
        full_remote_path = os.path.join(remote_toplevel_path, remote_path)
        # check that the path is valid and get the last modified time from the server
        remote_timestamp = datetime.datetime.fromtimestamp(int(os.path.getmtime(full_remote_path)))

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
        is_live=bool(host.hostname),
        # incremented with each update
        version=1,
        creator_ids=creator_ids if creator_ids is not None else [],
    )

    result = file_collection.insert_one(new_file_document.dict())
    if not result.acknowledged:
        raise OSError(f"db operation failed when trying to insert new file. Result: {result}")

    inserted_id = result.inserted_id

    new_directory = os.path.join(CONFIG.FILE_DIRECTORY, str(inserted_id))
    new_file_location = os.path.join(new_directory, filename)
    pathlib.Path(new_directory).mkdir(exist_ok=True)
    _sync_file_with_remote(full_remote_path, new_file_location)

    updated_file_entry = file_collection.find_one_and_update(
        {"_id": inserted_id, **get_default_permissions(user_only=False)},
        {
            "$set": {
                "location": new_file_location,
                "url_path": new_file_location,
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    sample_update_result = sample_collection.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {"$push": {"file_ObjectIds": inserted_id}},
    )
    if sample_update_result.modified_count != 1:
        raise OSError(
            f"db operation failed when trying to insert new file ObjectId into sample: {item_id}"
        )

    return updated_file_entry


def retrieve_file_path(file_ObjectId):
    file_collection = flask_mongo.db.files
    result = file_collection.find_one(
        {"_id": ObjectId(file_ObjectId), **get_default_permissions(user_only=False)}
    )
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
    from pydatalab.permissions import get_default_permissions

    item_id, file_id = ObjectId(item_id), ObjectId(file_id)
    sample_collection = flask_mongo.db.items
    file_collection = flask_mongo.db.files
    sample_result = sample_collection.update_one(
        {"item_id": item_id, **get_default_permissions(user_only=True)},
        {"$pull": {"file_ObjectIds": file_id}},
    )

    if sample_result.modified_count < 1:
        raise OSError(
            f"Failed to remove {file_id!r} from item {item_id!r}. Result: {sample_result.raw_result}"
        )

    file_collection.update_one(
        {"_id": file_id},
        {"$pull": {"item_ids": item_id}},
    )
