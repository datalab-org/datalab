from flask import Blueprint, jsonify
from werkzeug.exceptions import BadGateway

HEALTHCHECK = Blueprint("healthcheck", __name__)


@HEALTHCHECK.route("/healthcheck/is_ready", methods=["GET"])
def is_ready():
    from pydatalab.mongo import check_mongo_connection

    try:
        check_mongo_connection()
    except RuntimeError:
        raise BadGateway("Unable to connect to MongoDB at specified URI.") from None
    return (jsonify(status="success", message="Server and database are ready"), 200)


@HEALTHCHECK.route("/healthcheck/is_alive", methods=["GET"])
def is_alive():
    return (jsonify(status="success", message="Server is alive"), 200)
