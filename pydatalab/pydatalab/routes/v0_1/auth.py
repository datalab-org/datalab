"""This module implements functionality for authenticating users
via OAuth2 providers, and associating these OAuth2 identities
with their local accounts.

"""

import json
import random
from hashlib import sha512
from string import ascii_letters
from typing import Callable, Dict, Optional, Union

from bson import ObjectId
from flask import Blueprint, jsonify, redirect
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.github import github, make_github_blueprint
from flask_dance.contrib.orcid import make_orcid_blueprint, orcid
from flask_login import current_user, login_user
from flask_login.utils import LocalProxy

from pydatalab.config import CONFIG
from pydatalab.errors import UserRegistrationForbidden
from pydatalab.logger import LOGGER
from pydatalab.login import get_by_id_cached
from pydatalab.models.people import Identity, IdentityType, Person
from pydatalab.mongo import flask_mongo, insert_pydantic_model_fork_safe

KEY_LENGTH: int = 32


def wrapped_login_user(*args, **kwargs):
    LOGGER.warning("Logging in user %s with role %s", args[0].display_name, args[0].role)
    login_user(*args, **kwargs)


OAUTH_BLUEPRINTS: Dict[IdentityType, Blueprint] = {
    IdentityType.ORCID: make_orcid_blueprint(
        scope="/authenticate",
        sandbox=True,
    ),
    IdentityType.GITHUB: make_github_blueprint(
        scope="read:org,user",
    ),
}
"""A dictionary of Flask blueprints corresponding to the supported OAuth2 providers."""

OAUTH_PROXIES: Dict[IdentityType, LocalProxy] = {
    IdentityType.ORCID: orcid,
    IdentityType.GITHUB: github,
}
"""A dictionary of proxy objects (c.f. Flask context locals) corresponding
to the supported OAuth2 providers, and can be used to make further authenticated
requests out to the providers.
"""


def find_create_or_modify_user(
    identifier: str,
    identity_type: Union[str, IdentityType],
    identity_name: str,
    display_name: Optional[str] = None,
    verified: bool = False,
    create_account: bool = False,
) -> None:
    """Search for a user account with the given identifier and identity type, creating
    or connecting one if it does not exist.

        1. Find any user with the given identity, if found, return it.
        2. If no user exists, check if there is currently a user logged in:
            - If so, attach the identity to the current user.
            - If not, create an entry in the user database with this identity.
        3. Log in as the user for this session.

    """

    def find_user_with_identity(
        identifier: str,
        identity_type: Union[str, IdentityType],
    ) -> Optional[Person]:
        """Look up the given identity in the users database."""
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

            if not person.identities[identity_index].verified:
                flask_mongo.db.users.update_one(
                    {"_id": person.immutable_id},
                    {"$set": {f"identities.{identity_index}.verified": True}},
                )

            return person

        return None

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
        if use_display_name and identity.display_name:
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

    user = find_user_with_identity(identifier, identity_type)

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
            )
            current_user.refresh()
            user = current_user.person

        # If there is no current authenticated user, make one with the current OAuth identity
        else:
            if not create_account:
                raise UserRegistrationForbidden

            user = Person.new_user_from_identity(identity, use_display_name=True)
            wrapped_login_user(get_by_id_cached(str(user.immutable_id)))
            LOGGER.debug("Inserting new user model %s into database", user)
            insert_pydantic_model_fork_safe(user, "users")

    # Log the user into the session with this identity
    if user is not None:
        wrapped_login_user(get_by_id_cached(str(user.immutable_id)))


@oauth_authorized.connect_via(OAUTH_BLUEPRINTS[IdentityType.GITHUB])
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
    name = str(github_info["name"])

    org_membership = blueprint.session.get(f"/users/{username}/orgs").json()
    if CONFIG.GITHUB_ORG_ALLOW_LIST:
        create_account = any(
            str(org["id"]) in CONFIG.GITHUB_ORG_ALLOW_LIST for org in org_membership
        )
    else:
        create_account = False

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


@oauth_authorized.connect_via(OAUTH_BLUEPRINTS[IdentityType.ORCID])
def orcid_logged_in(_, token):
    """This signal hooks into any attempt to use the ORCID blueprint, and will
    associate a user account with this identity if not already present in the database.

    The OAuth token is not stored alongside the user.

    """
    if not token:
        return False

    find_create_or_modify_user(
        token["orcid"],
        IdentityType.ORCID,
        token["orcid"],
        display_name=token["name"],
        verified=True,
    )

    # Return false to prevent Flask-dance from trying to store the token elsewhere
    return False


@oauth_authorized.connect
def redirect_to_ui(blueprint, token):  # pylint: disable=unused-argument
    """Intercepts the default Flask-Dance and redirects to the referring page."""
    from flask import request

    referer = request.headers.get("Referer", "/")
    return redirect(referer)


def get_authenticated_user_info():
    """Returns metadata associated with the currently authenticated user."""
    if current_user.is_authenticated:
        return jsonify(json.loads(current_user.person.json())), 200
    else:
        return jsonify({"status": "failure", "message": "User must be authenticated."}), 401


def generate_user_api_key():
    """Returns metadata associated with the currently authenticated user."""
    if current_user.is_authenticated and current_user.role == "admin":
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


ENDPOINTS: Dict[str, Callable] = {
    "/get-current-user/": get_authenticated_user_info,
    "/get-api-key/": generate_user_api_key,
}
