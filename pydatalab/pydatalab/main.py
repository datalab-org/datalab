from typing import Any, Dict

from dotenv import dotenv_values
from flask import Flask, redirect, request, url_for
from flask_cors import CORS

import pydatalab.mongo
from pydatalab.config import CONFIG
from pydatalab.logger import logged_route
from pydatalab.utils import CustomJSONEncoder


def create_app(config_override: Dict[str, Any] = None) -> Flask:
    """Create the main `Flask` app with the given config.

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
    app.config.update(dotenv_values())

    if CONFIG.BEHIND_REVERSE_PROXY:
        # Fix headers for reverse proxied app:
        # https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)  # type: ignore

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
    )

    app.json_encoder = CustomJSONEncoder

    # Must use the full path so that this object can be mocked for testing
    flask_mongo = pydatalab.mongo.flask_mongo
    flask_mongo.init_app(app)
    register_endpoints(app)

    # Log whether the database is up or not, but do not crash out
    try:
        pydatalab.mongo.check_mongo_connection()
    except RuntimeError:
        pass

    @app.route("/")
    def index():
        """Landing page endpoint that renders a rudimentary welcome page based on the currently
        authenticated user.

        Warning:
            Does not use a Jinja template, so care must be taken in validating
            the embedded inputs.

        """
        from pydatalab.routes import (
            ENDPOINTS,  # pylint: disable=import-outside-toplevel
        )

        try:
            connected = pydatalab.mongo.check_mongo_connection()
        except RuntimeError:
            connected = False

        if connected:
            database_string = (
                '<p style="color: DarkSeaGreen">✅ Connected to underlying database</p>'
            )
        else:
            database_string = (
                '<p style="color: FireBrick">❎ Unable to connect to underlying database</p>'
            )

        return (
            f"""<h2><marquee width="200px"><p style="color: CornflowerBlue">Welcome to pydatalab</marquee></h2>
<h4>{database_string}</h4>
<h3>Available endpoints:</h3>
<ul>"""
            + "\n".join(
                [
                    f'<li><a href="{endp[0]}"><code><pre>{endp[0]}</pre></code></a></li>'
                    for endp in ENDPOINTS.items()
                ]
            )
            + "</ul>"
        )

    return app


def register_endpoints(app):
    from pydatalab.routes import ENDPOINTS  # pylint: disable=import-outside-toplevel

    for rule, func in ENDPOINTS.items():
        app.add_url_rule(rule, func.__name__, logged_route(func))


if __name__ == "__main__":
    app_ = create_app()
    app_.run(host="0.0.0.0", debug=CONFIG.DEBUG, port=5001)
