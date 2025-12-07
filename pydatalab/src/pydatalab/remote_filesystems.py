import datetime
import functools
import json
import multiprocessing
import os
import subprocess
import time
from typing import Any, Union

import pydatalab.mongo
from pydatalab.config import CONFIG, RemoteFilesystem
from pydatalab.logger import LOGGER


def get_directory_structures(
    directories: list[RemoteFilesystem],
    invalidate_cache: bool | None = None,
    parallel: bool = False,
) -> list[dict[str, Any]]:
    """For all registered top-level directories, call tree either
    locally or remotely to get their directory structures, or access
    the cached data for that directory, if it is available and fresh.

    Args:
        directories: The directories to scan.
        invalidate_cache: If true, then the cached directory structure will
            be reset, provided the cache was not updated very recently. If `False`,
            the cache will not be reset, even if it is older than the maximum configured
            age.
        parallel: If true, run each remote scraper in a new process.

    Returns:
        A lists of dictionaries for each specified top-level directory.

    """
    if not directories:
        return []

    if parallel:
        return multiprocessing.Pool(max(min(len(directories), 8), 1)).map(
            functools.partial(
                get_directory_structure,
                invalidate_cache=invalidate_cache,
            ),
            directories,
        )
    else:
        return [get_directory_structure(d, invalidate_cache=invalidate_cache) for d in directories]


def get_directory_structure(
    directory: RemoteFilesystem,
    invalidate_cache: bool | None = False,
    max_retries: int = 5,
) -> dict[str, Any]:
    """For the given remote directory, either reconstruct the directory
    structure in full, or access the cached version if is it recent
    enough.

    Any errors will be returned in the `contents` key for a given
    directory.

    Args:
        directory: A RemoteFilesystem object the directory to scan, with attributes
            `'name'`, `'path'` and optionally `'hostname'`.
        invalidate_cache: If `True`, then the cached directory structure will
            be reset, provided the cache was not updated very recently. If `False`,
            the cache will not be reset, even if it is older than the maximum configured
            age.
        max_retries: Used when called recursively to limit the number of attempts each PID
            will make to acquire the lock on the directory structure before returning an error.

    Returns:
        A dictionary with keys "name", "type" and "contents" for the
        top-level directory.

    """

    LOGGER.debug("Accessing directory structure of %s", directory)

    try:
        cached_dir_structure = _get_cached_directory_structure(directory)
        cache_last_updated = None
        if cached_dir_structure:
            cache_last_updated = cached_dir_structure["last_updated"]
            if cache_last_updated.tzinfo is None:
                cache_last_updated = cache_last_updated.replace(tzinfo=datetime.timezone.utc)
            cache_age = datetime.datetime.now(tz=datetime.timezone.utc) - cache_last_updated
            if invalidate_cache and cache_age < datetime.timedelta(
                minutes=CONFIG.REMOTE_CACHE_MIN_AGE
            ):
                LOGGER.debug(
                    "Not invalidating cache as its age (%s) is less than the configured %s.",
                    cache_age,
                    CONFIG.REMOTE_CACHE_MIN_AGE,
                )

        # If either:
        #     1) no cache for this directory,
        #     2) the cache is older than the max cache age and
        #        `invalidate_cache` has not been explicitly set to false,
        #     3) the `invalidate_cache` parameter is true, and the cache
        #        is older than the min age,
        # AND, if no other processes is updating the cache,
        # then rebuild the cache.
        if (
            (not cached_dir_structure)
            or (
                invalidate_cache is not False
                and cache_age > datetime.timedelta(minutes=CONFIG.REMOTE_CACHE_MAX_AGE)
            )
            or (
                invalidate_cache
                and cache_age > datetime.timedelta(minutes=CONFIG.REMOTE_CACHE_MIN_AGE)
            )
        ):
            owns_lock = _acquire_lock_dir_structure(directory)
            if owns_lock:
                dir_structure = _get_latest_directory_structure(directory.path, directory.hostname)
                # Save the directory structure to the database, which also releases the lock
                last_updated = _save_directory_structure(
                    directory,
                    dir_structure,
                )
                LOGGER.debug(
                    "Remote filesystems cache miss for '%s': last updated %s",
                    directory.name,
                    cache_last_updated,
                )
                status = "updated"
            else:
                if max_retries <= 0:
                    raise RuntimeError(
                        f"Failed to acquire lock for {directory.name} after the max number of attempts. This may indicate something wrong with the filesystem; please try again later."
                    )
                LOGGER.debug(
                    "PID %s waiting 5 seconds until FS %s is updated", os.getpid(), directory.name
                )
                time.sleep(5)
                return get_directory_structure(
                    directory, invalidate_cache=invalidate_cache, max_retries=max_retries - 1
                )

        else:
            last_updated = cached_dir_structure["last_updated"]
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=datetime.timezone.utc)
            dir_structure = cached_dir_structure["contents"]
            LOGGER.debug(
                "Remote filesystems cache hit for '%s': last updated %s",
                directory.name,
                last_updated,
            )
            status = "cached"

    except Exception as exc:
        dir_structure = [{"type": "error", "name": directory.name, "details": str(exc)}]
        last_updated = datetime.datetime.now(tz=datetime.timezone.utc)
        status = "error"

    finally:
        _release_lock_dir_structure(directory)

    return {
        "name": directory.name,
        "type": "toplevel",
        "contents": dir_structure,
        "last_updated": last_updated,
        "status": status,
    }


def _get_latest_directory_structure(
    directory_path: Union[str, "os.PathLike[str]"], hostname: str | None = None
) -> list[dict[str, str]]:
    """Call `tree` on the remote or mounted filesystem.

    If `directory_path` exists locally, then call tree directly,
    otherwise interpret the path as a remote.

    Args:
        directory_path: The path to the directory.
        hostname: The hostname of the remote server, if the path is remote.

    Returns:
        A dictionary of the `tree` output.

    """

    tree_command = ["tree", "-Jsf"]
    tree_timefmt = "%s"

    def _call_local_tree(directory_path: Union[str, "os.PathLike[str]"]) -> list[dict[str, Any]]:
        """Call `tree` in a local directory.

        Args:
            directory_path: The path to the folder on the local filesystem.

        Returns:
            A dictionary of the `tree` output.

        """
        command = tree_command + [str(directory_path), "--timefmt", tree_timefmt]
        process = subprocess.Popen(  # noqa: S603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        if stderr:
            raise RuntimeError(f"Local process {command!r} returned {stderr!r}.")

        return json.loads(stdout)

    def _call_remote_tree(
        directory_path: Union[str, "os.PathLike[str]"], hostname: str
    ) -> list[dict[str, Any]]:
        """Call `tree` on a remote system.

        Args:
            directory_path: The path to the folder on the remote filesystem.
            hostname: The hostname of the remote server.

        Returns:
            A dictionary of the `tree` output.

        """
        command = f"ssh {hostname} 'PATH=$PATH:~/ {' '.join(tree_command)} \"{directory_path}\" --timefmt {tree_timefmt}'"
        process = subprocess.Popen(  # noqa: S602,S607
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        LOGGER.debug("Calling %s", command)
        try:
            stdout, stderr = process.communicate(timeout=20)
        except Exception as exc:
            raise RuntimeError(f"Remote tree process {command!r} returned: {exc!r}")
        if stderr:
            # Do not return the bare stderr, but instead specialise the error message to common errors
            if "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!" in stderr.decode("utf-8"):
                msg = f"Remote host identification has changed for {hostname}: please contact the administrator of this datalab deployment."
                LOGGER.error(
                    "Remote host identification for %s has changed, failed to update remote directories",
                    hostname,
                )
            else:
                msg = "Remote tree process returned an error: please contact the administrator of this datalab deployment."
                LOGGER.error(
                    "Remote tree process on %s returned an error: %s",
                    hostname,
                    stderr.decode("utf-8"),
                )
            raise RuntimeError(msg)

        try:
            return json.loads(stdout)
        except Exception:
            if "error opening dir" in stdout.decode("utf-8"):
                msg = "Can no longer access the configured directory on the remote system; please contact the administrator of this datalab deployment."
                LOGGER.error(
                    "Remote directory %s on %s no longer accessible. Response: %s",
                    directory_path,
                    hostname,
                    stdout.decode("utf-8"),
                )
            else:
                msg = "Remote tree process failed with an unhandled error; please contact the administrator of this datalab deployment."
                LOGGER.error(
                    "Remote directory syncing for  %s on %s failed. Response: %s",
                    directory_path,
                    hostname,
                    stdout.decode("utf-8"),
                )

            raise RuntimeError(msg)

    if hostname:
        LOGGER.debug("Calling remote %s on %s", tree_command, directory_path)
        dir_structure = _call_remote_tree(directory_path, hostname)

    elif os.path.isdir(directory_path):
        dir_structure = _call_local_tree(directory_path)

    else:
        raise RuntimeError(f"Unable to find directory {directory_path!r} locally or remotely.")

    # `tree` returned [{"type": "unknown", "contents": [{"error": "opening dir"}]}] for errors
    # which needs to be handled here
    if dir_structure[0]["type"] == "unknown" and len(dir_structure[0].get("contents", [])) == 1:
        if "error" in dir_structure[0]["contents"][0]:
            raise RuntimeError(
                f"`tree` returned error for dir {dir_structure[0]['name']!r}: {dir_structure[0]['contents'][0]['error']!r}"
            )

    # because we used tree -f, the name: fields all contain full paths. We want to do a little re-arranging
    # so we get both a name, and a relative path field
    _fix_tree_paths(dir_structure[0]["contents"], directory_path)
    dir_tree = dir_structure[0]["contents"]

    return dir_tree


def _fix_tree_paths(
    subtree_list: list[dict[str, Any]], root_path: Union[str, "os.PathLike[str]"]
) -> None:
    """Adjusts in-place the output from `tree` to provide relative
    paths and names of each directory, rather than just the
    full path.

    Will be called recursively to descend into the `'contents'`
    key of each directory's info.

    Args:
        subtree_list: A list of `tree` outputs for directories.
        root_path: The path to use as the root of the relative paths.

    """
    for subtree in subtree_list:
        if "error" in subtree:
            continue

        full_path = subtree["name"]

        path, filename = os.path.split(full_path)

        escaped_path = path.replace(" ", r"\ ")
        relative_path = os.path.relpath(escaped_path, start=root_path)
        if relative_path == ".":
            relative_path = "/"
        else:
            relative_path = "/" + relative_path + "/"

        subtree["relative_path"] = relative_path
        subtree["name"] = filename
        if "contents" in subtree:
            _fix_tree_paths(subtree["contents"], root_path)


def _save_directory_structure(
    directory: RemoteFilesystem,
    dir_structure: list[dict[str, Any]],
) -> datetime.datetime:
    """Upserts the tree structure of each directory to the `remoteFilesystems`
    collection in the database.

    Args:
        directory: The remote filesystem object to update.
        dir_structure: The directory structure info.

    Returns:
        The last updated timestamp.

    """
    collection = pydatalab.mongo.get_database().remoteFilesystems

    last_updated = datetime.datetime.now(tz=datetime.timezone.utc)
    last_updated = last_updated.replace(microsecond=0)

    result = collection.update_one(
        {"name": directory.name},
        {
            "$set": {
                "contents": dir_structure,
                "last_updated": last_updated,
                "type": "toplevel",
                "_lock": None,
            }
        },
        upsert=True,
    )
    LOGGER.debug(
        "Result of saving directory %s structure to the db: %s %s",
        directory.name,
        last_updated,
        result.raw_result,
    )

    return last_updated


def _acquire_lock_dir_structure(
    directory: RemoteFilesystem,
) -> bool:
    """Attempt to acquire the lock on the directory structure to hint to other processes
    to not update it.

    Parameters:
        directory: The remote filesystem entry to lock.

    Returns:
        `True` if the lock was acquired, `False` otherwise.

    """
    client = pydatalab.mongo._get_active_mongo_client()
    with client.start_session() as session:
        collection = client.get_database().remoteFilesystems
        doc = collection.find_one({"name": directory.name}, projection=["_lock"], session=session)
        if doc and doc.get("_lock") is not None:
            pid = doc["_lock"].get("pid")
            ctime = doc["_lock"].get("ctime")
            lock_age = datetime.datetime.now(tz=datetime.timezone.utc) - ctime
            if lock_age > datetime.timedelta(minutes=CONFIG.REMOTE_CACHE_MIN_AGE):
                LOGGER.debug(
                    "Lock for %s already held by process %s for %s, forcing this process to acquire lock",
                    directory.name,
                    pid,
                    lock_age,
                )
            else:
                LOGGER.debug(
                    "Lock for %s already held by process %s since %s", directory.name, pid, ctime
                )
                return False

        collection.update_one(
            {"name": directory.name},
            {
                "$set": {
                    "_lock": {
                        "pid": os.getpid(),
                        "ctime": datetime.datetime.now(tz=datetime.timezone.utc),
                    }
                }
            },
            upsert=True,
            session=session,
        )
        LOGGER.debug("Acquired lock for %s as PID %s", directory.name, os.getpid())

    return True


def _release_lock_dir_structure(directory) -> bool:
    """Attempt to release the lock on the directory structure.

    Parameters:
        directory: The remote filesystem entry to lock.

    Returns:
        `True` if the lock was released successfully, `False` otherwise.

    """
    client = pydatalab.mongo._get_active_mongo_client()
    with client.start_session() as session:
        collection = client.get_database().remoteFilesystems
        doc = collection.find_one({"name": directory.name}, session=session)
        if doc:
            if doc.get("_lock") is not None:
                pid = doc["_lock"].get("pid")

                if pid != os.getpid():
                    LOGGER.debug(
                        "PID %s tried to release lock for %s, but lock was held by PID %s",
                        os.getpid(),
                        directory.name,
                        pid,
                    )
                    return False

            if doc.get("contents") is None:
                # If the lock is held by this process, but the directory structure has not been updated, then delete it
                collection.delete_one({"name": directory.name}, session=session)
                LOGGER.debug(
                    "PID %s is removed dir_structure stub %s",
                    os.getpid(),
                    doc,
                )
                return True

            # Otherwise just release the lock
            collection.update_one(
                {"name": directory.name}, {"$set": {"_lock": None}}, session=session
            )
            LOGGER.debug(
                "PID %s released locked on %s",
                os.getpid(),
                directory.name,
            )

    return True


def _get_cached_directory_structure(
    directory: RemoteFilesystem,
) -> dict[str, Any] | None:
    """Gets the structure of the given directory from the database.

    Args:
        directory: The configured RemoteFilesystem object to get.

    Returns:
        The stored directory structure.

    """
    collection = pydatalab.mongo.get_database().remoteFilesystems
    return collection.find_one({"name": directory.name})
