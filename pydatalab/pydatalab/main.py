import datetime
from typing import Any, Dict

from bson import json_util
from flask import Flask
from flask.json import JSONEncoder
from flask_cors import CORS

import pydatalab.mongo
from pydatalab.config import CONFIG


class CustomJSONEncoder(JSONEncoder):
    """Use a JSON encoder that can handle pymongo's bson."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime.datetime.isoformat(obj)
        return json_util.default(obj)


def create_app(config_override: Dict[str, Any] = None) -> Flask:
    """Create the `Flask` app with the given config.

    Parameters:
        config_override: Config value overrides to use
            within the `Flask` app.

    Returns:
        The `Flask` app with all associated endpoints.

    """

    app = Flask(__name__, instance_relative_config=True)

    if config_override:
        CONFIG.update(config_override)

    app.config.update(CONFIG.dict())
    CORS(app, resources={r"/*": {"origins": "*"}})

    app.json_encoder = CustomJSONEncoder

    # Must use the full path so that this object can be mocked for testing
    flask_mongo = pydatalab.mongo.flask_mongo
    flask_mongo.init_app(app)
    register_endpoints(app)

    @app.route("/")
    def index():
        return "Hello, This is a server"

    return app


def register_endpoints(app):
    from pydatalab.routes import ENDPOINTS  # pylint: disable=import-outside-toplevel

    for rule, func in ENDPOINTS.items():
        app.add_url_rule(rule, func.__name__, func)


if __name__ == "__main__":
    app_ = create_app()
    app_.run(host="0.0.0.0", debug=True, port=5001)
