import math
import os
from collections import Counter

from pydantic import BaseModel

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER

__all__ = ("FEATURE_FLAGS", "check_feature_flags", "FeatureFlags")


class AuthMechanisms(BaseModel):
    github: bool = False
    orcid: bool = False
    email: bool = False


class AIIntegrations(BaseModel):
    openai: bool = False
    anthropic: bool = False


class FeatureFlags(BaseModel):
    auth_mechanisms: AuthMechanisms = AuthMechanisms()
    ai_integrations: AIIntegrations = AIIntegrations()
    email_notifications: bool = False


FEATURE_FLAGS: FeatureFlags = FeatureFlags()
"""The global feature flags object.

This is a singleton of `FeatureFlags` that can be used to see
the enabled features of the app at a higher-level to the
configuration (e.g., includes runtime environment checks).
"""


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


def check_feature_flags(app):
    """Loop over various secrets and settings and populate the logs if
    missing or invalid, as well as setting the global `FEATURE_FLAGS`
    object reported by the API for use in UIs.

    """

    if CONFIG.EMAIL_AUTH_SMTP_SETTINGS is None:
        LOGGER.warning(
            "No email auth SMTP settings provided, email registration will not be enabled."
        )
    else:
        FEATURE_FLAGS.email_notifications = True
        if app.config["MAIL_SERVER"] and not app.config.get("MAIL_PASSWORD"):
            LOGGER.critical(
                "CONFIG.EMAIL_AUTH_SMTP_SETTINGS.MAIL_SERVER was set to '%s' but no `MAIL_PASSWORD` was provided. "
                "This can be passed in a `.env` file (as `MAIL_PASSWORD`) or as an environment variable.",
                app.config["MAIL_SERVER"],
            )
            FEATURE_FLAGS.email_notifications = False
        if not app.config["MAIL_DEFAULT_SENDER"]:
            LOGGER.critical(
                "CONFIG.EMAIL_AUTH_SMTP_SETTINGS.MAIL_DEFAULT_SENDER is not set in the config. "
                "Email authentication may not work correctly."
                "This can be set in the config above or equivalently via `MAIL_DEFAULT_SENDER` in a `.env` file, "
                "or as an environment variable."
            )
            FEATURE_FLAGS.email_notifications = False

        if (
            CONFIG.EMAIL_DOMAIN_ALLOW_LIST is None or CONFIG.EMAIL_DOMAIN_ALLOW_LIST
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

        _check_key_strength(CONFIG.SECRET_KEY)

    def _check_secret_and_warn(secret: str, error: str, environ: bool = False) -> bool:
        """Checks if a secret has been set, and if so, return True.

        Otherwise, warn and return False.

        Parameters:
            secret: The secret to check.
            error: The error message to log if the secret is missing.
            environ: Whether the secret should also be checked as an environment variable.
        """
        if not app.config.get(secret):
            LOGGER.warning("%s: please set `%s`", error, secret)
            return False
        if environ and not os.environ.get(secret):
            LOGGER.warning("%s: please set as an environment variable too `%s`", error, secret)
            return False

        return True

    if _check_secret_and_warn(
        "GITHUB_OAUTH_CLIENT_ID",
        "No GitHub OAuth client ID provided, GitHub login will not work",
    ) and _check_secret_and_warn(
        "GITHUB_OAUTH_CLIENT_SECRET",
        "No GitHub OAuth client secret provided, GitHub login will not work",
    ):
        FEATURE_FLAGS.auth_mechanisms.github = True
    if _check_secret_and_warn(
        "ORCID_OAUTH_CLIENT_SECRET",
        "No ORCID OAuth client secret provided, ORCID login will not work",
    ) and _check_secret_and_warn(
        "ORCID_OAUTH_CLIENT_ID", "No ORCID OAuth client ID provided, ORCID login will not work"
    ):
        FEATURE_FLAGS.auth_mechanisms.orcid = True
    if _check_secret_and_warn(
        "OPENAI_API_KEY",
        "No OpenAI API key provided, OpenAI-based ChatBlock will not work",
        environ=True,
    ):
        FEATURE_FLAGS.ai_integrations.openai = True
    if _check_secret_and_warn(
        "ANTHROPIC_API_KEY",
        "No Anthropic API key provided, Claude-based ChatBlock will not work",
        environ=True,
    ):
        FEATURE_FLAGS.ai_integrations.anthropic = True

    if CONFIG.DEBUG:
        LOGGER.warning("Running with debug logs enabled")

    if CONFIG.TESTING:
        LOGGER.critical(
            "Running in testing mode, with no authentication required; this is not recommended for production use: set `CONFIG.TESTING`"
        )

    if not CONFIG.DEPLOYMENT_METADATA:
        LOGGER.warning(
            "No deployment metadata provided, please set `CONFIG.DEPLOYMENT_METADATA` to allow the UI to provide helpful information to users"
        )

    if not CONFIG.APP_URL:
        LOGGER.warning(
            "Canonical URL for deployment is not set, please set `CONFIG.APP_URL` otherwise some features (redirects, email notifications) may not work correctly."
        )
