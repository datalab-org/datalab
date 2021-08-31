import datetime
from typing import Callable, Dict

from flask import jsonify

from pydatalab import remote_filesystems


def list_remote_directories():
    # all_directory_structures = remote_filesystems.get_all_directory_structures()
    all_directory_structures = remote_filesystems.get_all_directory_structures()
    return jsonify(all_directory_structures), 200


list_remote_directories.methods = ("GET",)  # type: ignore


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


list_remote_directories_cached.methods = ("GET",)  # type: ignore

ENDPOINTS: Dict[str, Callable] = {
    "/list-remote-directories/": list_remote_directories,
    "/list-remote-directories-cached/": list_remote_directories_cached,
}
