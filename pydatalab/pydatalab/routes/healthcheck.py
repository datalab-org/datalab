from typing import Callable, Dict

from flask import jsonify

from pydatalab.config import CONFIG


def is_ready():

    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure

    cli = MongoClient(
        CONFIG.MONGO_URI,
        connectTimeoutMS=100,
    )

    try:
        if cli.list_database_names():
            pass
    except ConnectionFailure:
        return (
            jsonify(status="error", message="Unable to connect to MongoDB at specified URI."),
            500,
        )

    return (jsonify(status="success", message="Server and database are ready"), 200)


def is_alive():
    return (jsonify(status="success", message="Server is alive"), 200)


is_alive.methods = ("GET",)  # type: ignore
is_ready.methods = ("GET",)  # type: ignore


ENDPOINTS: Dict[str, Callable] = {
    "/healthcheck/is_alive": is_alive,
    "/healthcheck/is_ready/": is_ready,
}
