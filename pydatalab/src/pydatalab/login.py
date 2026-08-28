"""This module implements functionality around the Flask-login manager,
for retrieving the authenticated user for a session and their identities.

"""

from enum import Enum
from hashlib import sha512
from typing import Any

from bson import ObjectId
from flask import g
from flask_login import LoginManager, UserMixin

from pydatalab.models import Person
from pydatalab.models.people import AccountStatus, Group, Identity, IdentityType
from pydatalab.models.utils import UserRole
from pydatalab.mongo import flask_mongo

__all__ = ("LOGIN_MANAGER",)


class AuthMethod(str, Enum):
    """Authentication source for the current request."""

    BROWSER_SESSION = "browser_session"
    PERMANENT_API_KEY = "permanent_api_key"
    TOOL_ACCESS_TOKEN = "tool_access_token"  # noqa: S105


class LoginUser(UserMixin):
    """A wrapper class around `Person` to allow flask-login to track
    the session of the current user and get their details
    from the database.

    (See https://flask-login.readthedocs.io/en/latest/#your-user-class)

    """

    id: str
    person: Person
    role: UserRole
    auth_method: AuthMethod

    def __init__(
        self,
        _id: str,
        data: Person,
        role: UserRole,
        auth_method: AuthMethod = AuthMethod.BROWSER_SESSION,
    ):
        """Construct the logged in user from a given ID and user data.

        Parameters:
            _id: The ID of the person in the database.
            data: The relevant metadata for this user, e.g., their identities, contact
                details, for use by the app.

        """
        self.id = _id
        self.person = data
        self.role = role
        self.auth_method = auth_method

    @property
    def display_name(self) -> str | None:
        """Returns the top-level display name for the user, if set."""
        return self.person.display_name

    @property
    def contact_email(self) -> str | None:
        """Returns the top-level contact email for the user, if set."""
        return self.person.contact_email

    @property
    def account_status(self) -> AccountStatus:
        """Returns the account status of the user."""
        return self.person.account_status

    @property
    def identities(self) -> list[Identity]:
        """Returns the list of identities of the user."""
        return self.person.identities

    @property
    def identity_types(self) -> list[IdentityType]:
        """Returns a list of the identity types associated with the user."""
        return [_.identity_type for _ in self.person.identities]

    @property
    def groups(self) -> list[Group] | None:
        """Returns the list of groups that the user is a member of."""
        return self.person.groups

    def refresh(self) -> None:
        """Reconstruct the user object from their database entry, to be used when,
        e.g., a new identity has been associated with them.
        """
        user = get_by_id(self.id)
        if user:
            self.person = user.person
            self.role = user.role


def groups_lookup() -> dict:
    return {
        "from": "groups",
        "let": {"group_ids": "$groups.immutable_id"},
        "pipeline": [
            {"$match": {"$expr": {"$in": ["$_id", {"$ifNull": ["$$group_ids", []]}]}}},
            {"$sort": {"__order": 1}},
            {"$project": {"_id": 1, "display_name": 1, "group_id": 1}},
        ],
        "as": "groups",
    }


def get_by_id(
    user_id: str | ObjectId,
    auth_method: AuthMethod = AuthMethod.BROWSER_SESSION,
) -> LoginUser | None:
    """Lookup the user database ID and create a new `LoginUser`
    with the relevant metadata.

    Parameters:
        user_id: The user's ID in the database, either as a string,
            an ObjectID, or a JSON `{'$oid': <id>}` dictionary.

    Raises:
        ValueError: if the user could not be found.

    """

    # Use next(..., None) rather than the cursor's .next() to avoid the case
    # where StopIteration is raised and not handled (e.g. manually deleted user,
    # tries to reconnect while the old cookies are still in the browser).
    cursor = flask_mongo.db.users.aggregate(
        [
            {"$match": {"_id": ObjectId(user_id)}},
            {"$lookup": groups_lookup()},
        ]
    )
    user = next(cursor, None)
    if not user:
        return None

    role = flask_mongo.db.roles.find_one({"_id": ObjectId(user_id)})
    if not role:
        role = "user"
    else:
        role = role["role"]

    return LoginUser(
        _id=str(user_id),
        data=Person(**user),
        role=UserRole(role),
        auth_method=auth_method,
    )


def get_by_api_key(api_credential: str) -> LoginUser | None:
    """Return the user authenticated by a DATALAB-API-KEY header value.

    The bearer value may be a permanent API key or a tool access token.
    """

    key_hash = sha512(api_credential.encode("utf-8")).hexdigest()
    user = flask_mongo.db.api_keys.find_one(
        {"hash": key_hash, "type": "api_key"},
        projection={"name": 0, "_id": 0, "digest": 0},
    )
    if user and user.get("user", False):
        return get_by_id(str(user["user"]), auth_method=AuthMethod.PERMANENT_API_KEY)

    legacy_user = flask_mongo.db.api_keys.find_one(
        {
            "hash": key_hash,
            "user_id": {"$exists": False},
            "name": {"$exists": False},
            "digest": {"$exists": False},
            "type": {"$exists": False},
        }
    )
    if legacy_user:
        return get_by_id(
            str(legacy_user["_id"]),
            auth_method=AuthMethod.PERMANENT_API_KEY,
        )

    from pydatalab.tools.grants import get_tool_access_token_user_id

    delegated_user_id = get_tool_access_token_user_id(api_credential)
    if delegated_user_id:
        delegated_user = get_by_id(delegated_user_id, auth_method=AuthMethod.TOOL_ACCESS_TOKEN)
        if delegated_user is not None and delegated_user.account_status == AccountStatus.ACTIVE:
            return delegated_user
    return None


def is_browser_session_user(user: Any) -> bool:
    """Return whether a request is authenticated by a datalab browser session."""
    return getattr(user, "auth_method", None) == AuthMethod.BROWSER_SESSION


def is_tool_access_token_user(user: Any) -> bool:
    """Return whether a request is authenticated by a tool access token."""
    return getattr(user, "auth_method", None) == AuthMethod.TOOL_ACCESS_TOKEN


LOGIN_MANAGER: LoginManager = LoginManager()
"""The global login manager for the app."""


@LOGIN_MANAGER.user_loader
def load_user(user_id: str) -> LoginUser | None:
    """Looks up the currently authenticated user and returns a `LoginUser` model."""
    g.api_key_session = False
    return get_by_id(str(user_id))


@LOGIN_MANAGER.request_loader
def request_loader(request) -> LoginUser | None:
    api_credential = request.headers.get("DATALAB-API-KEY", None)
    if api_credential:
        g.api_key_session = True
        return get_by_api_key(str(api_credential))
    return None
