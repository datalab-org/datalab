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
from typing import Dict, Optional, Union

import jwt
from bson import ObjectId
from flask import Blueprint, jsonify, redirect, request
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.github import github, make_github_blueprint
from flask_dance.contrib.orcid import make_orcid_blueprint, orcid
from flask_login import current_user, login_user
from flask_login.utils import LocalProxy

from pydatalab.config import CONFIG
from pydatalab.errors import UserRegistrationForbidden
from pydatalab.logger import LOGGER, logged_route
from pydatalab.login import get_by_id
from pydatalab.models.people import AccountStatus, Identity, IdentityType, Person
from pydatalab.mongo import flask_mongo, insert_pydantic_model_fork_safe
from pydatalab.send_email import send_mail

KEY_LENGTH: int = 32
LINK_EXPIRATION: datetime.timedelta = datetime.timedelta(hours=1)


@logged_route
def wrapped_login_user(*args, **kwargs):
    login_user(*args, **kwargs)


EMAIL_BLUEPRINT = Blueprint("email", __name__)

AUTH = Blueprint("auth", __name__)


OAUTH: Dict[IdentityType, Blueprint] = {
    IdentityType.ORCID: make_orcid_blueprint(
        scope="/authenticate",
        sandbox=os.environ.get("OAUTH_ORCID_SANDBOX", False),
    ),
    IdentityType.GITHUB: make_github_blueprint(
        scope="read:org,read:user",
    ),
    IdentityType.EMAIL: EMAIL_BLUEPRINT,
}
"""A dictionary of Flask blueprints corresponding to the supported OAuth providers."""

OAUTH_PROXIES: Dict[IdentityType, LocalProxy] = {
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


@logged_route
def find_user_with_identity(
    identifier: str,
    identity_type: Union[str, IdentityType],
    verify: bool = False,
) -> Optional[Person]:
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
            raise RuntimeError(
                "Unexpected error: multiple or no identities matched the OAuth token."
            )

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
    identity_type: Union[str, IdentityType],
    identity_name: str,
    display_name: Optional[str] = None,
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

    @logged_route
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
            raise RuntimeError(
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

    # Log the user into the session with this identity
    if user is not None:
        wrapped_login_user(get_by_id(str(user.immutable_id)))


@EMAIL_BLUEPRINT.route("/magic-link", methods=["POST"])
def generate_and_share_magic_link():
    """Generates a JWT-based magic link with which a user can log in, stores it
    in the database and sends it to the verified email address.

    """
    request_json = request.get_json()
    email = request_json.get("email")
    referrer = request_json.get("referrer")

    if not email:
        return jsonify({"status": "error", "detail": "No email provided."}), 400

    if not re.match(r"^\S+@\S+.\S+$", email):
        return jsonify({"status": "error", "detail": "Invalid email provided."}), 400

    if not referrer:
        LOGGER.warning("No referrer provided for magic link request: %s", request_json)
        return (
            jsonify(
                {
                    "status": "error",
                    "detail": "Referrer address not provided, please contact the datalab administrator.",
                }
            ),
            400,
        )

    # Generate a JWT for the user with a short expiration; the session itself
    # should persist
    # The key `exp` is a standard part of JWT; pyjwt treats this as an expiration time
    # and will correctly encode the datetime
    token = jwt.encode(
        {"exp": datetime.datetime.utcnow() + LINK_EXPIRATION, "email": email},
        CONFIG.SECRET_KEY,
        algorithm="HS256",
    )

    flask_mongo.db.magic_links.insert_one(
        {"jwt": token},
    )

    link = f"{referrer}?token={token}"

    instance_url = referrer.replace("https://", "")

    # See if the user already exists and adjust the email if so
    user = find_user_with_identity(email, IdentityType.EMAIL, verify=False)

    if not user:
        allowed = _check_email_domain(email, CONFIG.EMAIL_DOMAIN_ALLOW_LIST)
        if not allowed:
            LOGGER.info("Did not allow %s to register an account", email)
            return (
                jsonify(
                    {
                        "status": "error",
                        "detail": f"Email address {email} is not allowed to register an account. Please contact the administrator if you believe this is an error.",
                    }
                ),
                403,
            )

    if user is not None:
        subject = "Datalab Sign-in Magic Link"
        body = f"Click the link below to sign-in to the datalab instance at {instance_url}:\n\n{link}\n\nThis link is single-use and will expire in 1 hour."
    else:
        subject = "Datalab Registration Magic Link"
        body = f"Click the link below to register for the datalab instance at {instance_url}:\n\n{link}\n\nThis link is single-use and will expire in 1 hour."

    try:
        send_mail(email, subject, body)
    except Exception as exc:
        LOGGER.warning("Failed to send email to %s: %s", email, exc)
        return jsonify({"status": "error", "detail": "Email not sent successfully."}), 400

    return jsonify({"status": "success", "detail": "Email sent successfully."}), 200


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

    if datetime.datetime.fromtimestamp(data["exp"]) < datetime.datetime.utcnow():
        raise ValueError("Token expired, please request a new one.")

    email = data["email"]
    if not email:
        raise RuntimeError("No email found; please request a new token.")

    # If the email domain list is explicitly configured to None, this allows any
    # email address to make an active account, otherwise the email domain must match
    # the list of allowed domains and the admin must verify the user
    allowed = _check_email_domain(email, CONFIG.EMAIL_DOMAIN_ALLOW_LIST)
    if not allowed:
        # If this point is reached, the token is valid but the server settings have
        # changed since the link was generated, so best to fail safe
        raise UserRegistrationForbidden

    create_account = AccountStatus.UNVERIFIED
    if (
        CONFIG.EMAIL_DOMAIN_ALLOW_LIST is None
        or CONFIG.EMAIL_AUTO_ACTIVATE_ACCOUNTS
        or CONFIG.AUTO_ACTIVATE_ACCOUNTS
    ):
        create_account = AccountStatus.ACTIVE

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
    referer = request.headers.get("Referer", "/")
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
    referer = request.headers.get("Referer", "/")
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
        new_key = "".join(random.choices(ascii_letters, k=KEY_LENGTH))
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
