import datetime
import functools
import json
import multiprocessing
import os
import subprocess
from typing import Any, Dict, List, Optional, Union

import pydatalab.mongo
from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER


def get_directory_structures(
    directories: List[Dict[str, str]],
    invalidate_cache: Optional[bool] = None,
    parallel: bool = True,
) -> List[Dict[str, Any]]:
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
    if parallel:
        return multiprocessing.Pool(min(len(directories), 8)).map(
            functools.partial(
                get_directory_structure,
                invalidate_cache=invalidate_cache,
            ),
            directories,
        )
    else:
        return [get_directory_structure(d, invalidate_cache=invalidate_cache) for d in directories]


def get_directory_structure(
    directory: Dict[str, str],
    invalidate_cache: Optional[bool] = False,
) -> Dict[str, Any]:
    """For the given remote directory, either reconstruct the directory
    structure in full, or access the cached version if is it recent
    enough.

    Any errors will be returned in the `contents` key for a given
    directory.

    Args:
        directory: A dictionary describing the directory to scan, with keys
            `'name'`, `'path'` and optionally `'hostname'`.
        invalidate_cache: If `True`, then the cached directory structure will
            be reset, provided the cache was not updated very recently. If `False`,
            the cache will not be reset, even if it is older than the maximum configured
            age.

    Returns:
        A dictionary with keys "name", "type" and "contents" for the
        top-level directory.

    """

    LOGGER.debug(f"Accessing directory structure of {directory}")

    try:
        cached_dir_structure = _get_cached_directory_structure(directory)
        cache_last_updated = None
        if cached_dir_structure:
            cache_last_updated = cached_dir_structure["last_updated"]
            cache_age = datetime.datetime.now() - cached_dir_structure["last_updated"]
            if invalidate_cache and cache_age < datetime.timedelta(
                minutes=CONFIG.REMOTE_CACHE_MIN_AGE
            ):
                LOGGER.debug(
                    f"Not invalidating cache as its age ({cache_age=}) is less than the configured {CONFIG.REMOTE_CACHE_MIN_AGE=}."
                )

        # If either:
        #     1) no cache for this directory,
        #     2) the cache is older than the max cache age and
        #        `invalidate_cache` has not been explicitly set to false,
        #     3) the `invalidate_cache` parameter is true, and the cache
        #        is older than the min age,
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
            dir_structure = _get_latest_directory_structure(
                directory["path"], directory.get("hostname")
            )
            last_updated = _save_directory_structure(
                directory,
                dir_structure,
            )
            LOGGER.debug(
                "Remote filesystems cache miss for '%s': last updated %s",
                directory["name"],
                cache_last_updated,
            )

        else:
            last_updated = cached_dir_structure["last_updated"]
            dir_structure = cached_dir_structure["contents"]
            LOGGER.debug(
                "Remote filesystems cache hit for '%s': last updated %s",
                directory["name"],
                last_updated,
            )

    except RuntimeError as exc:
        dir_structure = [{"type": "error", "details": str(exc)}]
        last_updated = datetime.datetime.now()

    return {
        "name": directory["name"],
        "type": "toplevel",
        "contents": dir_structure,
        "last_updated": last_updated,
    }


def _get_latest_directory_structure(
    directory_path: Union[str, "os.PathLike[str]"], hostname: str = None
) -> List[Dict[str, str]]:
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

    def _call_local_tree(directory_path: Union[str, "os.PathLike[str]"]) -> List[Dict[str, Any]]:
        """Call `tree` in a local directory.

        Args:
            directory_path: The path to the folder on the local filesystem.

        Returns:
            A dictionary of the `tree` output.

        """
        command = tree_command + [str(directory_path), "--timefmt", tree_timefmt]
        process = subprocess.Popen(
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
    ) -> List[Dict[str, Any]]:
        """Call `tree` on a remote system.

        Args:
            directory_path: The path to the folder on the remote filesystem.
            hostname: The hostname of the remote server.

        Returns:
            A dictionary of the `tree` output.

        """
        command = f"ssh {hostname} 'PATH=$PATH:~/ {' '.join(tree_command)} \"{directory_path}\" --timefmt {tree_timefmt}'"
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        LOGGER.debug(f"Calling {command}")
        stdout, stderr = process.communicate(timeout=10)
        if stderr:
            raise RuntimeError(f"Remote tree process {command!r} returned: {stderr!r}")

        return json.loads(stdout)

    if hostname:
        LOGGER.debug(f"Calling remote {tree_command} on {directory_path}")
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
    subtree_list: List[Dict[str, Any]], root_path: Union[str, "os.PathLike[str]"]
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
    directory: Dict[str, Any],
    dir_structure: List[Dict[str, Any]],
) -> datetime.datetime:
    """Upserts the tree structure of each directory to the `remoteFilesystems`
    collection in the database.

    Args:
        directory_name: The top-level directory name to update.
        dir_structure: The directory structure info.

    Returns:
        The last updated timestamp.

    """
    collection = pydatalab.mongo._get_active_mongo_client().get_database().remoteFilesystems

    last_updated = datetime.datetime.now()
    last_updated = last_updated.replace(microsecond=0)

    result = collection.update_one(
        {"name": directory["name"]},
        {
            "$set": {
                "contents": dir_structure,
                "last_updated": last_updated,
                "type": "toplevel",
            }
        },
        upsert=True,
    )
    LOGGER.debug(
        "Result of saving directory %s structure to the db: %s %s",
        directory["name"],
        last_updated,
        result.raw_result,
    )

    return last_updated


def _get_cached_directory_structure(
    directory: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Gets the structure of the given directory from the database.

    Args:
        directory_name: The name of the directory to get.

    Returns:
        The stored directory structure.

    """
    collection = pydatalab.mongo._get_active_mongo_client().get_database().remoteFilesystems
    return collection.find_one({"name": directory["name"]})
