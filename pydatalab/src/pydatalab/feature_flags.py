import math
import os
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER

__all__ = (
    "AI_API_KEY_ENV_VARS",
    "FEATURE_FLAGS",
    "RUNTIME_CONFIG_ENV_VARS",
    "check_feature_flags",
    "FeatureFlags",
)


class AuthMechanisms(BaseModel):
    github: bool = False
    orcid: bool = False
    email: bool = False
    google: bool = False
    microsoft: bool = False


class AIIntegrations(BaseModel):
    openai: bool = False
    anthropic: bool = False


class FeatureFlags(BaseModel):
    auth_mechanisms: AuthMechanisms = AuthMechanisms()
    login_only_auth_mechanisms: list[str] = []
    ai_integrations: AIIntegrations = AIIntegrations()
    email_notifications: bool = False
    tags: bool = False
    ungrouped_inventory: Literal["none", "warn", "error"] = "none"


FEATURE_FLAGS: FeatureFlags = FeatureFlags()
"""The global feature flags object.

This is a singleton of `FeatureFlags` that can be used to see
the enabled features of the app at a higher-level to the
configuration (e.g., includes runtime environment checks).
"""

# Flask and ServerConfig automatically load FLASK_ and PYDATALAB_ variables. Unprefixed
# integration variables (mail settings, OAuth credentials, and AI API keys) are not loaded
# automatically, so define them here to copy them into app.config and keep runtime loading
# and feature checks in sync.
_MAIL_CONFIG_ENV_VARS = ("MAIL_PASSWORD", "MAIL_DEFAULT_SENDER")

_OAUTH_INTEGRATIONS = (
    (
        "github",
        "GitHub login",
        ("GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_CLIENT_SECRET"),
    ),
    (
        "google",
        "Google login",
        ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"),
    ),
    (
        "microsoft",
        "Microsoft login",
        ("MICROSOFT_OAUTH_CLIENT_ID", "MICROSOFT_OAUTH_CLIENT_SECRET"),
    ),
    (
        "orcid",
        "ORCID login",
        ("ORCID_OAUTH_CLIENT_ID", "ORCID_OAUTH_CLIENT_SECRET"),
    ),
)

_AI_INTEGRATIONS = (
    ("openai", "OpenAI integration", "OPENAI_API_KEY"),
    ("anthropic", "Anthropic integration", "ANTHROPIC_API_KEY"),
)

AI_API_KEY_ENV_VARS = tuple(api_key for _, _, api_key in _AI_INTEGRATIONS)
RUNTIME_CONFIG_ENV_VARS = (
    *_MAIL_CONFIG_ENV_VARS,
    *(
        variable
        for _, _, required_variables in _OAUTH_INTEGRATIONS
        for variable in required_variables
    ),
    *AI_API_KEY_ENV_VARS,
)


def _check_key_strength(s: str, min_entropy: float = 3.8) -> None:
    (
        """Compute the Shannon entropy of a string and raise a `RuntimeError` if it is below a threshold.""",
    )

    def shannon_entropy(s: str) -> float:
        return sum(-math.log2(c / len(s)) * (c / len(s)) for c in Counter(s).values())

    if shannon_entropy(s) < min_entropy:
        raise RuntimeError(
            f"`SECRET_KEY` does not have enough Shannon entropy ({shannon_entropy(s)} vs {min_entropy}), please set `CONFIG.SECRET_KEY` or the `PYDATALAB_SECRET_KEY` environment variable to a more secure value."
        )


def _check_config_vars_and_warn(
    app,
    required_variables: tuple[str, ...],
    feature: str,
    *,
    require_environment: bool = False,
) -> bool:
    """Return whether all variables required by an integration are available."""
    for variable in required_variables:
        if not app.config.get(variable):
            LOGGER.warning("%s will not work: please set `%s`", feature, variable)
            return False
        if require_environment and not os.environ.get(variable):
            LOGGER.warning(
                "%s will not work: please also set `%s` as an environment variable",
                feature,
                variable,
            )
            return False

    return True


def check_feature_flags(app):
    """Loop over various secrets and settings and populate the logs if
    missing or invalid, as well as setting the global `FEATURE_FLAGS`
    object reported by the API for use in UIs.

    """

    FEATURE_FLAGS.tags = CONFIG.ENABLE_TAGS
    FEATURE_FLAGS.login_only_auth_mechanisms = [
        method.value for method in (CONFIG.LOGIN_ONLY_AUTH_METHODS or [])
    ]
    FEATURE_FLAGS.ungrouped_inventory = CONFIG.UNGROUPED_INVENTORY

    if CONFIG.EMAIL_AUTH_SMTP_SETTINGS is None:
        LOGGER.warning(
            "No email auth SMTP settings provided, email registration will not be enabled."
        )
    else:
        mail_password_env_var, mail_default_sender_env_var = _MAIL_CONFIG_ENV_VARS
        FEATURE_FLAGS.email_notifications = True
        if app.config["MAIL_SERVER"] and not app.config.get(mail_password_env_var):
            LOGGER.critical(
                "CONFIG.EMAIL_AUTH_SMTP_SETTINGS.MAIL_SERVER was set to '%s' but no `%s` was provided. "
                "This can be passed in a `.env` file (as `%s`) or as an environment variable.",
                app.config["MAIL_SERVER"],
                mail_password_env_var,
                mail_password_env_var,
            )
            FEATURE_FLAGS.email_notifications = False
        if not app.config[mail_default_sender_env_var]:
            LOGGER.critical(
                "CONFIG.EMAIL_AUTH_SMTP_SETTINGS.%s is not set in the config. "
                "Email authentication may not work correctly."
                "This can be set in the config above or equivalently via `%s` in a `.env` file, "
                "or as an environment variable.",
                mail_default_sender_env_var,
                mail_default_sender_env_var,
            )
            FEATURE_FLAGS.email_notifications = False

        if CONFIG.DISABLE_MAGIC_LINK_AUTH:
            FEATURE_FLAGS.auth_mechanisms.email = False
            LOGGER.warning(
                "`CONFIG.DISABLE_MAGIC_LINK_AUTH` is set; email magic-link authentication will not be enabled."
            )
        elif (
            CONFIG.EMAIL_DOMAIN_ALLOW_LIST is None
            or CONFIG.EMAIL_DOMAIN_ALLOW_LIST
            # Login-only email does not need any domains allowed for registration
            or "email" in FEATURE_FLAGS.login_only_auth_mechanisms
        ) and FEATURE_FLAGS.email_notifications:
            FEATURE_FLAGS.auth_mechanisms.email = True
        else:
            LOGGER.warning(
                "`CONFIG.EMAIL_DOMAIN_ALLOW_LIST` is unset or empty; email registration will not be enabled."
            )

    if CONFIG.IDENTIFIER_PREFIX == "test":
        LOGGER.critical(
            "You should configure an identifier prefix for this deployment. "
            "You should attempt to make it unique to your deployment or group. "
            "In the future these will be optionally globally validated versus all deployments for uniqueness. "
            "For now the value of %s will be used.",
            CONFIG.IDENTIFIER_PREFIX,
        )

    if not CONFIG.TESTING:
        if not CONFIG.SECRET_KEY:
            raise RuntimeError(
                "No secret key provided, please set `CONFIG.SECRET_KEY` or the `PYDATALAB_SECRET_KEY` environment variable."
            )

        if os.environ.get("PYDATALAB_ALLOW_INSECURE_SECRET_KEY") == "1":
            LOGGER.critical(
                "Insecure secret key allowed via `PYDATALAB_ALLOW_INSECURE_SECRET_KEY`, this MUST NOT be used in production."
            )
            return

        _check_key_strength(CONFIG.SECRET_KEY)

    for mechanism, feature, required_variables in _OAUTH_INTEGRATIONS:
        if _check_config_vars_and_warn(app, required_variables, feature):
            setattr(FEATURE_FLAGS.auth_mechanisms, mechanism, True)

    for integration, feature, api_key in _AI_INTEGRATIONS:
        if _check_config_vars_and_warn(app, (api_key,), feature, require_environment=True):
            setattr(FEATURE_FLAGS.ai_integrations, integration, True)
    if CONFIG.DEBUG:
        LOGGER.warning("Running with debug logs enabled")

    if CONFIG.TESTING:
        LOGGER.critical(
            "Running in testing mode (deterministic secret key, backups disabled, @datalab.test users can log in with tokens minted by invoke tasks); this is not recommended for production use: unset `CONFIG.TESTING`"
        )

    if not CONFIG.DEPLOYMENT_METADATA:
        LOGGER.warning(
            "No deployment metadata provided, please set `CONFIG.DEPLOYMENT_METADATA` to allow the UI to provide helpful information to users"
        )

    if not CONFIG.APP_URL:
        LOGGER.warning(
            "Canonical URL for deployment is not set, please set `CONFIG.APP_URL` otherwise some features (redirects, email notifications) may not work correctly."
        )
