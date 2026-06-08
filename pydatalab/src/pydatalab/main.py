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
    app.config.update(CONFIG.model_dump())

    # This value will still be overwritten by any dotenv values
    app.config["MAIL_DEBUG"] = app.config.get("MAIL_DEBUG") or CONFIG.TESTING

    # percolate datalab mail settings up to the `MAIL_` env vars/app config
    # for use by Flask Mail
    if CONFIG.EMAIL_AUTH_SMTP_SETTINGS is not None:
        mail_settings = CONFIG.EMAIL_AUTH_SMTP_SETTINGS.model_dump()
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

    if CONFIG.USE_X_ACCEL_REDIRECT and not CONFIG.BEHIND_REVERSE_PROXY:
        # X-Accel-Redirect hands downloads off to nginx; without a proxy in front
        # to intercept the header, clients would receive empty-bodied responses.
        LOGGER.warning(
            "USE_X_ACCEL_REDIRECT is enabled but BEHIND_REVERSE_PROXY is False: "
            "file/export downloads will return empty responses unless an nginx "
            "proxy is configured to honour the X-Accel-Redirect header."
        )

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
    pydatalab.mongo.run_startup_migrations()

    if CONFIG.FILE_DIRECTORY is not None:
        pathlib.Path(CONFIG.FILE_DIRECTORY).mkdir(parents=False, exist_ok=True)

    # Register any custom item models declared in the config so that they are
    # served via the generic item endpoints and appear in `/info/types`.
    from pydatalab.models import load_custom_item_models

    load_custom_item_models(CONFIG.CUSTOM_ITEM_MODELS)

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

        # Human-readable labels for providers whose blueprint name doesn't title-case
        # nicely; anything not listed falls back to `key.title()`.
        provider_labels = {"orcid": "ORCID", "github": "GitHub"}

        def provider_label(identity_type) -> str:
            key = getattr(identity_type, "value", identity_type)
            return provider_labels.get(key, key.title())

        app_link_string = ""
        if CONFIG.APP_URL:
            app_link_string = f'<p><a href="{CONFIG.APP_URL}">Go to the web app</a></p>'

        links = []
        identities_string = ""

        if connected:
            if current_user.is_authenticated:
                welcome_string = f"<h2>Hello, {current_user.display_name}!</h2>"

                # List the already-connected identities by provider.
                identities = "".join(
                    f"<li>{provider_label(identity.identity_type)}: {identity.name}</li>"
                    for identity in current_user.identities
                )
                identities_string = f"<h3>Connected identities:</h3><ul>{identities}</ul>"

                # Offer a connect link for each provider not yet linked.
                for identity_type in OAUTH_PROXIES:
                    if identity_type not in current_user.identity_types:
                        key = getattr(identity_type, "value", identity_type)
                        links.append(
                            f"<a href={url_for(f'{key}.login')}>Connect {provider_label(identity_type)}</a>"
                        )
                links.append(f"<a href={url_for('logout')}>Log out</a>")
            else:
                welcome_string = (
                    "<h2>Welcome!</h2><h4>Please connect an OAuth account to continue:</h4>"
                )
                for identity_type in OAUTH_PROXIES:
                    key = getattr(identity_type, "value", identity_type)
                    links.append(
                        f"<a href={url_for(f'{key}.login')}>Login via {provider_label(identity_type)}</a>"
                    )
        else:
            welcome_string = ""

        links_string = "<ul>" + "".join(f"<li>{link}</li>" for link in links) + "</ul>"

        return f"""
            <h2><p style="color: CornflowerBlue">Welcome to pydatalab</p></h2>
<p>{welcome_string}</p>
{app_link_string}
{identities_string}
{links_string}
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
