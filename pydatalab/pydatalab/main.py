import datetime
from typing import Any, Dict

from dotenv import dotenv_values
from flask import Flask, redirect, request, session, url_for
from flask_compress import Compress
from flask_cors import CORS
from flask_login import current_user, logout_user
from werkzeug.middleware.proxy_fix import ProxyFix

import pydatalab.mongo
from pydatalab.config import CONFIG
from pydatalab.logger import logged_route
from pydatalab.login import LOGIN_MANAGER
from pydatalab.utils import CustomJSONEncoder

compress = Compress()


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
    flask_mongo.init_app(app, connectTimeoutMS=100, serverSelectionTimeoutMS=100)

    register_endpoints(app)

    LOGIN_MANAGER.init_app(app)

    pydatalab.mongo.create_default_indices()

    compress.init_app(app)

    @app.route("/logout")
    def logout():
        """Logs out the local user from the current session."""
        logout_user()
        return redirect(request.environ.get("HTTP_REFERER", "/"))

    @app.before_first_request  # runs before FIRST request (only once)
    def make_session_permanent():
        """Make the session permanent so that it doesn't expire on browser close, but instead adds a lifetime."""
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(days=1)

    @app.route("/")
    def index():
        """Landing page endpoint that renders a rudimentary welcome page based on the currently
        authenticated user.

        Warning:
            Does not use a Jinja template, so care must be taken in validating
            the embedded inputs.

        """
        from pydatalab.routes import (  # pylint: disable=import-outside-toplevel
            ENDPOINTS,
            auth,
        )

        OAUTH_PROXIES = auth.OAUTH_PROXIES

        connected = True
        try:
            pydatalab.mongo.check_mongo_connection()
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

        if connected:
            if current_user.is_authenticated:
                welcome_string = f"""
                    <h2>Hello, {current_user.display_name}!</h2>
                    <h3>Connected identities:</h3>
                    <ul>
                """

                for identity in current_user.identities:
                    if identity.identity_type == "github":
                        welcome_string += f"""
                            <li>
                                <a href="https://github.com/{identity.name}">
                                    <i class="fa fa-github"></i>
                                    {identity.name}
                                </a>
                            </li>
                        """

                    elif identity.identity_type == "orcid":
                        welcome_string += f"""
                            <li>
                                <a href="https://orcid.org/{identity.name}">
                                    <img alt="ORCID logo" style="vertical-align: middle;", src="https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png" width="16" height="16" />
                                    {identity.name}
                                </a>
                            </li>
                        """

                welcome_string += "</ul>"

            else:
                welcome_string = (
                    """<h2>Welcome!</h2><h4>Please connect an OAuth account to continue:</h4>"""
                )

            connect_buttons = {
                "github": f"""
                    <a href={url_for('github.login')}>
                        <i class="fa fa-github"></i>
                        Connect GitHub
                    </a></br>
                """,
                "orcid": f"""
                    <a href={url_for("orcid.login")}>
                        <img alt="ORCID logo" style="vertical-align: middle;", src="https://info.orcid.org/wp-content/uploads/2019/11/orcid_16x16.png" width="16" height="16" />
                        Connect ORCID
                    </a></br>
                """,
            }

            auth_string = "<ul>"
            logout_string = ""

            if current_user.is_authenticated:
                for k in OAUTH_PROXIES:
                    if k not in current_user.identity_types:
                        auth_string += f"<li>{connect_buttons[k]}</li>"
                logout_string += f'<a href={url_for("logout")}>Log out</a>'

            else:
                for k in OAUTH_PROXIES:
                    auth_string += f'<li>{connect_buttons[k].replace("Connect", "Login via")}</li>'

            auth_string += "</ul>"

            endpoints_string = "\n".join(
                [
                    f'<li><a href="{endp[0]}"><pre>{endp[0]}</pre></a></li>'
                    for endp in ENDPOINTS.items()
                ]
            )
            endpoints_string = f"""<h3>Available endpoints:</h3><ul>{endpoints_string}</ul>"""

        else:
            auth_string = ""
            logout_string = ""
            welcome_string = ""
            endpoints_string = ""

        return f"""<head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
            </head>
            <h2><p style="color: CornflowerBlue">Welcome to pydatalab</p></h2>
<p>{welcome_string}</p>
<p>{auth_string}</p>
<p>{logout_string}</p>
<h3>API status:</h3>
<h4>{database_string}</h4>
{endpoints_string}
"""

    return app


def register_endpoints(app: Flask):
    """Loops through the implemented endpoints, blueprints and error handlers adds them to the app."""
    from pydatalab.errors import ERROR_HANDLERS
    from pydatalab.routes import ENDPOINTS, __api_version__, auth

    OAUTH_BLUEPRINTS = auth.OAUTH_BLUEPRINTS

    for rule, func in ENDPOINTS.items():
        major, minor, patch = __api_version__.split(".")
        versions = ["", f"/v{major}", f"/v{major}.{minor}", f"/v{major}.{minor}.{patch}"]
        for ver in versions:
            app.add_url_rule(
                f"{ver}{rule}",
                f"{ver}{rule}",
                logged_route(func),
            )

    for bp in OAUTH_BLUEPRINTS:
        app.register_blueprint(OAUTH_BLUEPRINTS[bp], url_prefix="/login")

    for exception_type, handler in ERROR_HANDLERS:
        app.register_error_handler(exception_type, handler)


if __name__ == "__main__":
    app_ = create_app()
    app_.run(host="0.0.0.0", debug=CONFIG.DEBUG, port=5001)
