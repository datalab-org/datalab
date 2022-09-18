from typing import Callable, Dict

from flask import jsonify, request

from pydatalab.config import CONFIG
from pydatalab.remote_filesystems import get_directory_structures


def list_remote_directories():
    """Returns the most recent directory structures from the server.

    If the cache is missing or is older than some configured time,
    then it will be reconstructed.

    """
    invalidate_cache = None
    if "invalidate_cache" in request.args:
        invalidate_cache = request.args["invalidate_cache"]
        if invalidate_cache not in ("1", "0"):
            return jsonify({"error": "invalidate_cache must be 0 or 1"}), 400
        invalidate_cache = bool(int(invalidate_cache))

    all_directory_structures = get_directory_structures(
        CONFIG.REMOTE_FILESYSTEMS, invalidate_cache=invalidate_cache
    )

    response = {}
    response["meta"] = {}
    response["meta"]["remotes"] = CONFIG.REMOTE_FILESYSTEMS
    if all_directory_structures:
        oldest_update = min(d["last_updated"] for d in all_directory_structures)
        response["meta"]["oldest_cache_update"] = oldest_update.isoformat()
        response["data"] = all_directory_structures
    return jsonify(response), 200


list_remote_directories.methods = ("GET",)  # type: ignore


ENDPOINTS: Dict[str, Callable] = {
    "/list-remote-directories/": list_remote_directories,
}
