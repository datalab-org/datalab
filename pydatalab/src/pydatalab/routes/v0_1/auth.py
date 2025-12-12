"""This module implements functionality for authenticating users
via OAuth2 providers and JWT, and associating these identities
with their local accounts.

"""

import datetime
import json
import os
import random
import re
from hashlib import sha512
from string import ascii_letters

import jwt
from bson import ObjectId
from flask import Blueprint, g, jsonify, redirect, request
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized
from flask_login import current_user, login_user
from flask_login.utils import LocalProxy
from werkzeug.exceptions import BadRequest, Forbidden

from pydatalab.config import CONFIG
from pydatalab.errors import UserRegistrationForbidden
from pydatalab.feature_flags import FEATURE_FLAGS
from pydatalab.logger import LOGGER
from pydatalab.login import get_by_id
from pydatalab.models.people import AccountStatus, Identity, IdentityType, Person
from pydatalab.mongo import flask_mongo, insert_pydantic_model_fork_safe
from pydatalab.send_email import send_mail

KEY_LENGTH: int = 32
LINK_EXPIRATION: datetime.timedelta = datetime.timedelta(hours=1)


def make_github_blueprint(
    client_id=None,
    client_secret=None,
    *,
    authorization_url_params=None,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with GitHub using OAuth 2. This requires
    a client ID and client secret from GitHub. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`GITHUB_OAUTH_CLIENT_ID` and
    :envvar:`GITHUB_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on GitHub.
        client_secret (str): The client secret for your application on GitHub
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/github``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/github/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    github_bp = OAuth2ConsumerBlueprint(
        "github",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.github.com/",
        authorization_url="https://github.com/login/oauth/authorize",  # noqa: S105
        authorization_url_params=authorization_url_params,
        token_url="https://github.com/login/oauth/access_token",  # noqa: S106
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    github_bp.from_config["client_id"] = "GITHUB_OAUTH_CLIENT_ID"
    github_bp.from_config["client_secret"] = "GITHUB_OAUTH_CLIENT_SECRET"  # noqa: S105

    @github_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_github = github_bp.session

    return github_bp


github = LocalProxy(lambda: g.flask_dance_github)


def make_orcid_blueprint(
    client_id=None,
    client_secret=None,
    *,
    authorization_url_params=None,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
    sandbox=False,
):
    """
    Make a blueprint for authenticating with ORCID (https://orcid.org)
    using OAuth2.

    This requires a client ID and client secret from ORCID. You should
    either pass them to this constructor, or make sure that your Flask
    application config defines them, using the variables
    :envvar:`ORCID_OAUTH_CLIENT_ID` and :envvar:`ORCID_OAUTH_CLIENT_SECRET`.

    The ORCID Sandbox API (https://sandbox.orcid.org) will be used if
    the ``sandbox`` argument is set to true.

    Args:
        client_id (str): The client ID for your application on ORCID.
        client_secret (str): The client secret for your application on ORCID
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/orcid``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/orcid/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.
        sandbox (bool): Whether to use the ORCID sandbox instead of the production API.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """

    base_url = "https://api.orcid.org"
    authorization_url = "https://orcid.org/oauth/authorize"
    token_url = "https://orcid.org/oauth/token"  # noqa: S105
    if sandbox:
        base_url = "https://api.sandbox.orcid.org"
        authorization_url = "https://sandbox.orcid.org/oauth/authorize"
        token_url = "https://sandbox.orcid.org/oauth/token"  # noqa: S105

    orcid_bp = OAuth2ConsumerBlueprint(
        "orcid",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=base_url,
        authorization_url=authorization_url,
        authorization_url_params=authorization_url_params,
        token_url=token_url,
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    orcid_bp.from_config["client_id"] = "ORCID_OAUTH_CLIENT_ID"
    orcid_bp.from_config["client_secret"] = "ORCID_OAUTH_CLIENT_SECRET"  # noqa: S105

    @orcid_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_orcid = orcid_bp.session

    return orcid_bp


orcid = LocalProxy(lambda: g.flask_dance_orcid)


def wrapped_login_user(*args, **kwargs):
    login_user(*args, **kwargs)


EMAIL_BLUEPRINT = Blueprint("email", __name__)

AUTH = Blueprint("auth", __name__)


OAUTH: dict[IdentityType, Blueprint] = {
    IdentityType.ORCID: make_orcid_blueprint(
        scope="openid",
        authorization_url_params={"prompt": "login"},
        sandbox=os.environ.get("OAUTH_ORCID_SANDBOX", False),
    ),
    IdentityType.GITHUB: make_github_blueprint(
        authorization_url_params={"prompt": "select_account"},
        scope="read:org,read:user",
    ),
    IdentityType.EMAIL: EMAIL_BLUEPRINT,
}
"""A dictionary of Flask blueprints corresponding to the supported OAuth providers."""

OAUTH_PROXIES: dict[IdentityType, LocalProxy] = {
    IdentityType.ORCID: orcid,
    IdentityType.GITHUB: github,
}
"""A dictionary of proxy objects (c.f. Flask context locals) corresponding
to the supported OAuth2 providers, and can be used to make further authenticated
requests out to the providers.
"""


def _check_email_domain(email: str, allow_list: list[str] | None) -> bool:
    """Checks whether the provided email address is allowed to
    register an account based on the configured domain allow list.

    If the configured allow list is None, any email address is allowed to register.
    If it is an empty list, no email addresses are allowed to register.

    If the user already exists, they will be allowed to login either way.

    Parameters:
        email: The email address to check.
        allow_list: The list of allowed domains.

    Returns:
        Whether the email address is allowed to register an account.

    """
    if CONFIG.TESTING:
        return True

    domain = email.split("@")[-1]
    if isinstance(allow_list, list) and not allow_list:
        return False

    if allow_list is None:
        return True

    for allowed in allow_list:
        if domain.endswith(allowed):
            break
    else:
        if allow_list:
            return False

    return True


def find_user_with_identity(
    identifier: str,
    identity_type: str | IdentityType,
    verify: bool = False,
) -> Person | None:
    """Look up the given identity in the users database.

    Parameters:
        identifier: The identifier of the identity to look up.
        identity_type: The type of the identity to look up.
        verify: Whether to mark the identity as verified if it is found.

    """
    user = flask_mongo.db.users.find_one(
        {"identities.identifier": identifier, "identities.identity_type": identity_type},
    )
    if user:
        person = Person(**user)
        identity_indices: list[int] = [
            ind
            for ind, _ in enumerate(person.identities)
            if (_.identity_type == identity_type and _.identifier == identifier)
        ]
        if len(identity_indices) != 1:
            raise BadRequest("Unexpected error: multiple or no identities matched the OAuth token.")

        identity_index = identity_indices[0]

        if verify and not person.identities[identity_index].verified:
            flask_mongo.db.users.update_one(
                {"_id": person.immutable_id},
                {"$set": {f"identities.{identity_index}.verified": True}},
            )

        return person

    return None


def find_create_or_modify_user(
    identifier: str,
    identity_type: str | IdentityType,
    identity_name: str,
    display_name: str | None = None,
    verified: bool = False,
    create_account: bool | AccountStatus = False,
) -> None:
    """Search for a user account with the given identifier and identity type, creating
    or connecting one if it does not exist.

        1. Find any user with the given identity, if found, return it.
        2. If no user exists, check if there is currently a user logged in:
            - If so, attach the identity to the current user.
            - If not, create an entry in the user database with this identity.
        3. Log in as the user for this session.

    """

    def attach_identity_to_user(
        user_id: str,
        identity: Identity,
        use_display_name: bool = False,
        use_contact_email: bool = False,
    ) -> None:
        """Associates an OAuth ID with a user entry in the database.

        This function is currently brittle and would need to be updated
        if the corresponding `Person` schema changes due to the hard-coded
        field names.

        Parameters:
            user_id: The database ID of the user as a string.
            identity: The identity to associate.
            use_display_name: Whether to set the user's top-level display name with a
                display name provided by this identity.
            use_contact_email: Whether to set the user's top-level contact email with
                an email address provided by this identity.

        Raises:
            RuntimeError: If the update was unsuccessful.

        """
        update = {"$push": {"identities": identity.dict()}}
        if use_display_name and identity and identity.display_name:
            update["$set"] = {"display_name": identity.display_name}

        if use_contact_email and identity.identity_type is IdentityType.EMAIL and identity.verified:
            update["$set"] = {"contact_email": identity.identifier}

        result = flask_mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            update,
        )

        if result.matched_count != 1:
            raise BadRequest(
                f"Attempted to modify user {user_id} but performed {result.matched_count} updates. Results:\n{result.raw_result}"
            )

    user = find_user_with_identity(identifier, identity_type, verify=True)

    # If no user was found in the database with the OAuth ID, make or modify one:
    if not user:
        identity = Identity(
            identifier=identifier,
            identity_type=identity_type,
            name=identity_name,
            display_name=display_name,
            verified=verified,
        )

        # If there is currently a user logged in who has gone through OAuth with a new identity,
        # then update the user database with the identity
        if current_user.is_authenticated:
            attach_identity_to_user(
                current_user.id,
                identity,
                use_display_name=True if current_user.display_name is None else False,
                use_contact_email=True if current_user.contact_email is None else False,
            )
            current_user.refresh()
            user = current_user.person

        # If there is no current authenticated user, make one with the current OAuth identity
        else:
            if not create_account:
                raise UserRegistrationForbidden

            if isinstance(create_account, bool):
                account_status = AccountStatus.UNVERIFIED
            else:
                account_status = create_account

            user = Person.new_user_from_identity(
                identity, use_display_name=True, account_status=account_status
            )
            LOGGER.debug("Inserting new user model %s into database", user)
            insert_pydantic_model_fork_safe(user, "users")
            user_model = get_by_id(str(user.immutable_id))
            if user is None:
                raise RuntimeError("Failed to insert user into database")

            wrapped_login_user(user_model)
            # Send email notification to admins
            _send_admin_email_notification(user)

    if user is not None and user.account_status == AccountStatus.DEACTIVATED:
        _send_admin_email_notification(user)

    # Log the user into the session with this identity
    if user is not None:
        wrapped_login_user(get_by_id(str(user.immutable_id)))


def _validate_magic_link_request(email: str, referrer: str) -> None:
    if not email:
        raise BadRequest("No email provided")

    if not re.match(r"^\S+@\S+.\S+$", email):
        raise BadRequest("Invalid email provided.")

    if not referrer:
        raise BadRequest("Referrer address not provided, please contact the datalab administrator")


def _generate_and_store_token(email: str, intent: str = "register") -> str:
    """Generate a JWT for the user with a short expiration and store it in the session.

    The session itself persists beyond the JWT expiration. The `exp` key is a standard
    part of JWT that PyJWT treats as an expiration time and will correctly encode the datetime.

    Args:
        email: The user's email address to include in the token.
        intent: The intent of the magic link, e.g., "register" "verify", or "login".

    Returns:
        The generated JWT token string.

    """
    payload = {
        "exp": datetime.datetime.now(datetime.timezone.utc) + LINK_EXPIRATION,
        "email": email,
        "intent": intent,
    }

    token = jwt.encode(
        payload,
        CONFIG.SECRET_KEY,
        algorithm="HS256",
    )

    flask_mongo.db.magic_links.insert_one({"jwt": token})

    return token


def _check_user_registration_allowed(email: str) -> None:
    user = find_user_with_identity(email, IdentityType.EMAIL, verify=False)

    if not user:
        allowed = _check_email_domain(email, CONFIG.EMAIL_DOMAIN_ALLOW_LIST)
        if not allowed:
            LOGGER.warning("Did not allow %s to register an account", email)
            raise Forbidden(
                f"Email address {email} is not allowed to register an account. Please contact the administrator if you believe this is an error."
            )


def _send_admin_email_notification(user: Person) -> None:
    """Sends an email notification to the admin email address when an unverified user
    attempts to register an account.

    """
    if not FEATURE_FLAGS.email_notifications:
        LOGGER.info("Email notifications are disabled; not sending unverified user notification.")
        return

    admins = flask_mongo.db.users.aggregate(
        [
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "role",
                }
            },
            {"$unwind": "$role"},
            {"$match": {"role.role": "admin"}},
        ]
    )

    admin_emails = [a["contact_email"] for a in admins if a.get("contact_email")]

    # Get contact emails of admin users via lookup in the roles and users collections
    if user.account_status == AccountStatus.UNVERIFIED:
        subject = "User Registration Notification"
        subject += f": {CONFIG.APP_URL}" if CONFIG.APP_URL else ""
        body = (
            f"A new user with display name {user.display_name} attempted to register an account on {CONFIG.APP_URL}.\n\n"
            "Please review the registration in your admin panel and verify the user if appropriate."
        )

    elif user.account_status == AccountStatus.DEACTIVATED:
        subject = "Deactivated User Login Attempt Notification"
        subject += f": {CONFIG.APP_URL}" if CONFIG.APP_URL else ""
        body = (
            f"A deactivated user with display name {user.display_name} attempted to log in to the datalab instance at {CONFIG.APP_URL}.\n\n"
            "No action is required unless you wish to reactivate this user."
        )

    elif user.account_status == AccountStatus.ACTIVE:
        subject = "New User Created"
        subject += f": {CONFIG.APP_URL}" if CONFIG.APP_URL else ""
        body = (
            f"A new user with display name {user.display_name} has registered on the datalab instance at {CONFIG.APP_URL}.\n\n"
            "No action is required unless you wish to deactivate this user."
        )

    else:
        LOGGER.critical("Unknown user status %s for new user %s", user.account_status, user)
        return

    try:
        for email in admin_emails:
            send_mail(email, subject, body)
    except Exception as exc:
        LOGGER.warning("Failed to send unverified user notification email: %s", exc)


def _send_magic_link_email(
    email: str, token: str, referrer: str | None, purpose: str = "authorize"
) -> None:
    if not referrer:
        referrer = "https://example.com"

    link = f"{referrer}?token={token}"
    instance_url = referrer.replace("https://", "")

    if purpose == "authorize":
        user = find_user_with_identity(email, IdentityType.EMAIL, verify=False)
        if user is not None:
            subject = "datalab Sign-in Magic Link"
            body = f"Click the link below to sign-in to the datalab instance at {instance_url}:\n\n{link}\n\nThis link is single-use and will expire in 1 hour."
        else:
            subject = "datalab Registration Magic Link"
            body = f"Click the link below to register for the datalab instance at {instance_url}:\n\n{link}\n\nThis link is single-use and will expire in 1 hour."

    elif purpose == "verify":
        subject = "datalab Email Address Verification"
        body = f"Click the link below to verify your email address for the datalab instance at {instance_url}:\n\n{link}\n\nThis link is single-use and will expire in 1 hour."

    else:
        LOGGER.critical("Unknown purpose %s for magic link email", purpose)
        raise RuntimeError("Unknown error occurred")

    try:
        send_mail(email, subject, body)
    except Exception as exc:
        LOGGER.warning("Failed to send email to %s: %s", email, exc)
        raise RuntimeError("Email not sent successfully.")


@EMAIL_BLUEPRINT.route("/magic-link", methods=["POST"])
def generate_and_share_magic_link():
    """Generates a JWT-based magic link with which a user can log in, stores it
    in the database and sends it to the verified email address.

    """

    request_json = request.get_json()
    email = request_json.get("email")
    referrer = request_json.get("referrer")

    _validate_magic_link_request(email, referrer)
    _check_user_registration_allowed(email)
    token = _generate_and_store_token(email, intent="register")
    _send_magic_link_email(email, token, referrer)

    return jsonify({"status": "success", "message": "Email sent successfully."}), 200


@EMAIL_BLUEPRINT.route("/email")
def email_logged_in():
    """Endpoint for handling magic link authentication.

    - Checks the passed token for as valid JWT in the `magic_links` collection
    - If found, checks if the user with the decoded email exists in the user
    collection.
    - If not found, make the user account and verify their email address,
    - Authenticate the user for this session.

    """
    args = request.args
    token = args.get("token")
    if not token:
        raise ValueError("Token not provided")

    if not flask_mongo.db.magic_links.find_one({"jwt": token}):
        raise ValueError("Token not found, please request a new one.")

    data = jwt.decode(
        token,
        CONFIG.SECRET_KEY,
        algorithms=["HS256"],
    )

    if datetime.datetime.fromtimestamp(
        data["exp"], tz=datetime.timezone.utc
    ) < datetime.datetime.now(tz=datetime.timezone.utc):
        raise ValueError("Token expired, please request a new one.")

    email = data["email"]
    if not email:
        raise BadRequest("No email found; please request a new token.")

    # If the email domain list is explicitly configured to None, this allows any
    # email address to make an active account, otherwise the email domain must match
    # the list of allowed domains and the admin must verify the user

    if data.get("intent") == "register":
        allowed = _check_email_domain(email, CONFIG.EMAIL_DOMAIN_ALLOW_LIST)
        if not allowed:
            raise UserRegistrationForbidden

        create_account = AccountStatus.UNVERIFIED
        if (
            CONFIG.EMAIL_DOMAIN_ALLOW_LIST is None
            or CONFIG.EMAIL_AUTO_ACTIVATE_ACCOUNTS
            or CONFIG.AUTO_ACTIVATE_ACCOUNTS
        ):
            create_account = AccountStatus.ACTIVE

    else:
        create_account = False

    find_create_or_modify_user(
        email,
        IdentityType.EMAIL,
        email,
        display_name=email,
        verified=True,
        create_account=create_account,
    )

    if CONFIG.APP_URL:
        return redirect(CONFIG.APP_URL, 307)
    referer = request.headers.get("Referer", CONFIG.ROOT_PATH or "/")
    return redirect(referer, 307)


@oauth_authorized.connect_via(OAUTH[IdentityType.GITHUB])
def github_logged_in(blueprint, token):
    """This Flask signal hooks into any attempt to use the GitHub blueprint, and will
    make a user account with this identity if not already present in the database.

    Makes one authorized request to the GitHub API to get the user's GitHub ID,
    username and display name, without storing the OAuth token.

    """
    if not token:
        return False

    resp = blueprint.session.get("/user")
    if not resp.ok:
        return False

    github_info = resp.json()
    github_user_id = str(github_info["id"])
    username = str(github_info["login"])
    name = str(github_info["name"] if github_info["name"] is not None else github_info["login"])

    create_account: bool | AccountStatus = False
    # Use the read:org scope to check if the user is a member of at least one of the allowed orgs
    if CONFIG.GITHUB_ORG_ALLOW_LIST:
        for org in CONFIG.GITHUB_ORG_ALLOW_LIST:
            if str(int(org)) == org:
                org = int(org)
            if blueprint.session.get(f"/orgs/{org}/members/{username}").ok:
                # If this person has a GH account on the org allow list, activate their account
                create_account = AccountStatus.ACTIVE
                break

    elif CONFIG.GITHUB_ORG_ALLOW_LIST is None:
        create_account = True

    if CONFIG.GITHUB_AUTO_ACTIVATE_ACCOUNTS or CONFIG.AUTO_ACTIVATE_ACCOUNTS:
        create_account = AccountStatus.ACTIVE

    find_create_or_modify_user(
        github_user_id,
        IdentityType.GITHUB,
        username,
        display_name=name,
        verified=True,
        create_account=create_account,
    )

    # Return false to prevent Flask-dance from trying to store the token elsewhere
    return False


@oauth_authorized.connect_via(OAUTH[IdentityType.ORCID])
def orcid_logged_in(_, token):
    """This signal hooks into any attempt to use the ORCID blueprint, and will
    associate a user account with this identity if not already present in the database.

    The OAuth token is not stored alongside the user.

    """
    if not token:
        return False

    # New ORCID accounts must be activated by an admin unless configured otherwise
    create_account = AccountStatus.UNVERIFIED
    if CONFIG.ORCID_AUTO_ACTIVATE_ACCOUNTS or CONFIG.AUTO_ACTIVATE_ACCOUNTS:
        create_account = AccountStatus.ACTIVE

    find_create_or_modify_user(
        token["orcid"],
        IdentityType.ORCID,
        token["orcid"],
        display_name=token.get("name", token["orcid"]),
        verified=True,
        create_account=create_account,
    )

    # Return false to prevent Flask-dance from trying to store the token elsewhere
    return False


@oauth_authorized.connect
def redirect_to_ui(blueprint, token):  # pylint: disable=unused-argument
    """Intercepts the default Flask-Dance and redirects to the referring page."""
    if CONFIG.APP_URL:
        return redirect(CONFIG.APP_URL, 307)
    referer = request.headers.get("Referer", CONFIG.ROOT_PATH or "/")
    return redirect(referer, 307)


@AUTH.route("/get-current-user/", methods=["GET"])
def get_authenticated_user_info():
    """Returns metadata associated with the currently authenticated user."""
    if current_user.is_authenticated:
        current_user_response = json.loads(current_user.person.json())
        current_user_response["role"] = current_user.role.value
        return jsonify(current_user_response), 200
    else:
        return jsonify({"status": "failure", "message": "User must be authenticated."}), 401


@AUTH.route("/get-api-key/", methods=["GET"])
def generate_user_api_key():
    """Returns metadata associated with the currently authenticated user."""
    if current_user.is_authenticated:
        new_key = "".join(random.choices(ascii_letters, k=KEY_LENGTH))  # noqa: S311
        flask_mongo.db.api_keys.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {"hash": sha512(new_key.encode("utf-8")).hexdigest()}},
            upsert=True,
        )
        return jsonify({"key": new_key}), 200
    else:
        return (
            jsonify(
                {
                    "status": "failure",
                    "message": "User must be an authenticated admin to request an API key.",
                }
            ),
            401,
        )


@AUTH.route("/testing/create-magic-link", methods=["POST"])
def create_test_magic_link():
    """Create a magic link for testing purposes.

    This endpoint is only available when TESTING=True.
    It creates a user with the specified email and role, generates a magic link,
    and returns the token.
    """
    if not CONFIG.TESTING:
        return jsonify(
            {"status": "error", "detail": "This endpoint is only available in testing mode."}
        ), 403

    request_json = request.get_json()
    email = request_json.get("email")
    referrer = request_json.get("referrer", "http://localhost:8080")

    _validate_magic_link_request(email, referrer)

    token = _generate_and_store_token(email, intent="register")

    return jsonify({"status": "success", "token": token}), 200
