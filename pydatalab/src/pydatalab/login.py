"""This module implements functionality around the Flask-login manager,
for retrieving the authenticated user for a session and their identities.

"""

from hashlib import sha512

from bson import ObjectId
from flask_login import LoginManager, UserMixin

from pydatalab.models import Person
from pydatalab.models.people import AccountStatus, Group, Identity, IdentityType
from pydatalab.models.utils import UserRole
from pydatalab.mongo import flask_mongo

__all__ = ("LOGIN_MANAGER",)


class LoginUser(UserMixin):
    """A wrapper class around `Person` to allow flask-login to track
    the session of the current user and get their details
    from the database.

    (See https://flask-login.readthedocs.io/en/latest/#your-user-class)

    """

    id: str
    person: Person
    role: UserRole

    def __init__(
        self,
        _id: str,
        data: Person,
        role: UserRole,
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


def get_by_id_cached(user_id):
    """Cached version of get_by_id."""
    return get_by_id(user_id)


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


def get_by_id(user_id: str) -> LoginUser | None:
    """Lookup the user database ID and create a new `LoginUser`
    with the relevant metadata.

    Parameters:
        user_id: The user's ID in the database, either as a string,
            an ObjectID, or a JSON `{'$oid': <id>}` dictionary.

    Raises:
        ValueError: if the user could not be found.

    """

    user = flask_mongo.db.users.aggregate(
        [
            {"$match": {"_id": ObjectId(user_id)}},
            {"$lookup": groups_lookup()},
        ]
    ).next()
    if not user:
        return None

    role = flask_mongo.db.roles.find_one({"_id": ObjectId(user_id)})
    if not role:
        role = "user"
    else:
        role = role["role"]

    return LoginUser(_id=user_id, data=Person(**user), role=UserRole(role))


def get_by_api_key(key: str):
    """Checks if the hashed version of the key is in the keys collection,
    if so, return the authenticated user.

    """

    hash = sha512(key.encode("utf-8")).hexdigest()
    user = flask_mongo.db.api_keys.find_one({"hash": hash}, projection={"hash": 0})
    if user:
        return get_by_id_cached(str(user["_id"]))


LOGIN_MANAGER: LoginManager = LoginManager()
"""The global login manager for the app."""


@LOGIN_MANAGER.user_loader
def load_user(user_id: str) -> LoginUser | None:
    """Looks up the currently authenticated user and returns a `LoginUser` model."""
    return get_by_id_cached(str(user_id))


@LOGIN_MANAGER.request_loader
def request_loader(request) -> LoginUser | None:
    api_key = request.headers.get("DATALAB-API-KEY", None)
    if api_key:
        return get_by_api_key(str(api_key))
    return None
