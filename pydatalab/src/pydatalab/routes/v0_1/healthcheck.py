from flask import Blueprint, jsonify

HEALTHCHECK = Blueprint("healthcheck", __name__)


@HEALTHCHECK.route("/healthcheck/is_ready", methods=["GET"])
def is_ready():
    from pydatalab.mongo import check_mongo_connection

    try:
        check_mongo_connection()
    except RuntimeError:
        return (
            jsonify(status="error", message="Unable to connect to MongoDB at specified URI."),
            502,
        )
    return (jsonify(status="success", message="Server and database are ready"), 200)


@HEALTHCHECK.route("/healthcheck/is_alive", methods=["GET"])
def is_alive():
    return (jsonify(status="success", message="Server is alive"), 200)
