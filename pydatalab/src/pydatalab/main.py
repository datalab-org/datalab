import datetime
import logging
import os
import pathlib
from typing import Any

from dotenv import dotenv_values
from flask import Flask, redirect, request, url_for
from flask_compress import Compress
from flask_cors import CORS
from flask_login import current_user, logout_user
from werkzeug.middleware.proxy_fix import ProxyFix

import pydatalab.mongo
from pydatalab import __version__
from pydatalab.config import CONFIG
from pydatalab.feature_flags import check_feature_flags
from pydatalab.logger import LOGGER, setup_log
from pydatalab.login import LOGIN_MANAGER
from pydatalab.send_email import MAIL
from pydatalab.utils import BSONProvider

COMPRESS = Compress()


def create_app(
    config_override: dict[str, Any] | None = None, env_file: pathlib.Path | None = None
) -> Flask:
    """Create the main `Flask` app with the given config.

    Parameters:
        config_override: Config value overrides to use
            within the `Flask` app.

    Returns:
        The `Flask` app with all associated endpoints.

    """
    setup_log("werkzeug", log_level=logging.INFO)
    setup_log("", log_level=logging.INFO)

    app = Flask(__name__, instance_relative_config=True)

    if config_override:
        CONFIG.update(config_override)

    app.config.from_prefixed_env()
    app.config.update(CONFIG.dict())

    # This value will still be overwritten by any dotenv values
    app.config["MAIL_DEBUG"] = app.config.get("MAIL_DEBUG") or CONFIG.TESTING

    # percolate datalab mail settings up to the `MAIL_` env vars/app config
    # for use by Flask Mail
    if CONFIG.EMAIL_AUTH_SMTP_SETTINGS is not None:
        mail_settings = CONFIG.EMAIL_AUTH_SMTP_SETTINGS.dict()
        for key in mail_settings:
            app.config[key] = mail_settings[key]

    # Load config values from a provided .env file into the flask app config
    # This useful for non-datalab settings like OAuth secrets
    if isinstance(env_file, bool) and not env_file:
        # If env_file is explicitly set to, do not load any .env file
        LOGGER.info("Not loading any env file")
    else:
        app.config.update(dotenv_values(dotenv_path=env_file))

    # Testing config: to enable OAuth2 on dev servers without https, we need to control the
    # OAUTHLIB_INSECURE_TRANSPORT setting. If this is provided in the .env file, we also need
    # to set it as an environment variable for the underlying oauthlib library to pick it up
    if app.config.get("OAUTHLIB_INSECURE_TRANSPORT"):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = app.config["OAUTHLIB_INSECURE_TRANSPORT"]

    # Set LLM API keys as env vars if present in the flask config
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if app.config.get(key):
            os.environ[key] = app.config[key]

    LOGGER.info("Launching datalab version %s", __version__)
    LOGGER.info("Starting app with Flask app.config: %s", app.config)

    check_feature_flags(app)

    if CONFIG.BEHIND_REVERSE_PROXY:
        # Fix headers for reverse proxied app:
        # https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)  # type: ignore

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
    )

    # Override the default provider with a version that can handle ObjectIDs and returns isofromat dates
    app.json = BSONProvider(app)

    # Make the session permanent so that it doesn't expire on browser close, but instead adds a lifetime
    app.permanent_session_lifetime = datetime.timedelta(hours=CONFIG.SESSION_LIFETIME)

    # Must use the full path so that this object can be mocked for testing
    flask_mongo = pydatalab.mongo.flask_mongo
    flask_mongo.init_app(app, connectTimeoutMS=100, serverSelectionTimeoutMS=100)

    for extension in (LOGIN_MANAGER, MAIL, COMPRESS):
        extension.init_app(app)

    pydatalab.mongo.create_default_indices()

    if CONFIG.FILE_DIRECTORY is not None:
        pathlib.Path(CONFIG.FILE_DIRECTORY).mkdir(parents=False, exist_ok=True)

    register_endpoints(app)
    LOGGER.info("App created.")

    @app.route(f"{CONFIG.ROOT_PATH}logout")
    def logout():
        """Logs out the local user from the current session."""
        logout_user()
        return redirect(request.environ.get("HTTP_REFERER", "/"))

    @app.route(CONFIG.ROOT_PATH)
    def index():
        """Landing page endpoint that renders a rudimentary welcome page based on the currently
        authenticated user.

        Warning:
            Does not use a Jinja template, so care must be taken in validating
            the embedded inputs.

        """
        from pydatalab.routes import OAUTH_PROXIES

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
                    <a href={url_for("github.login")}>
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
                logout_string += f"<a href={url_for('logout')}>Log out</a>"

            else:
                for k in OAUTH_PROXIES:
                    auth_string += f"<li>{connect_buttons[k].replace('Connect', 'Login via')}</li>"

            auth_string += "</ul>"

        else:
            auth_string = ""
            logout_string = ""
            welcome_string = ""

        return f"""<head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
            </head>
            <h2><p style="color: CornflowerBlue">Welcome to pydatalab</p></h2>
<p>{welcome_string}</p>
<p>{auth_string}</p>
<p>{logout_string}</p>
<h3>API status:</h3>
<h4>{database_string}</h4>
"""

    return app


def register_endpoints(app: Flask):
    """Loops through the implemented endpoints, blueprints and error handlers adds them to the app."""
    from pydatalab.errors import ERROR_HANDLERS
    from pydatalab.routes import BLUEPRINTS, OAUTH, __api_version__

    major, minor, patch = __api_version__.split(".")
    versions = ["", f"v{major}", f"v{major}.{minor}", f"v{major}.{minor}.{patch}"]

    for bp in BLUEPRINTS:
        for ver in versions:
            app.register_blueprint(
                bp, url_prefix=f"{CONFIG.ROOT_PATH}{ver}", name=f"{ver}/{bp.name}"
            )

    for bp in OAUTH:  # type: ignore
        app.register_blueprint(OAUTH[bp], url_prefix=f"{CONFIG.ROOT_PATH}login")  # type: ignore

    for exception_type, handler in ERROR_HANDLERS:
        app.register_error_handler(exception_type, handler)
