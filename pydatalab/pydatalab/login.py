"""This module implements functionality around the Flask-login manager,
for retrieving the authenticated user for a session and their identities.

"""

from enum import Enum
from functools import lru_cache
from typing import Dict, List, Literal, Optional, Union

from bson import ObjectId
from flask_login import LoginManager, UserMixin

from pydatalab.logger import LOGGER
from pydatalab.models import Person
from pydatalab.models.people import Identity, IdentityType
from pydatalab.mongo import flask_mongo

__all__ = ("LOGIN_MANAGER",)


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


class LoginUser(UserMixin):
    """A wrapper class around `Person` to allow flask-login to track
    the session of the current user and get their details
    from the database.

    (See https://flask-login.readthedocs.io/en/latest/#your-user-class)

    """

    id: str
    person: Person
    role: UserRole

    def __init__(self, _id: Union[str, ObjectId], data: Union[dict, Person, None] = None):
        """Construct the logged in user from a given ID and user data.

        Parameters:
            _id: The ID of the person in the database.
            data: The relevant metadata for this user, e.g., their identities, contact
                details, for use by the app.

        """
        self.id = str(_id)
        if data is None:
            data = self.get_by_id(self.id)
            if data is None:
                raise RuntimeError(f"No user entry found with ID {self.id}")
            else:
                self.person = data.person
        else:
            if isinstance(data, Person):
                self.person = data
            else:
                self.person = Person(**data)

        role = flask_mongo.db.roles.find_one({"_id": ObjectId(self.id)})
        if not role:
            self.role = UserRole.USER
        else:
            self.role = UserRole(role["role"])

        if self.role == UserRole.ADMIN:
            LOGGER.warning(f"User {self.person.display_name} logged in as an admin.")

        LOGGER.warning(f"User {self.person.display_name} logged in as an {self.role}.")

    def get_id(self):
        """Returns the database ID of the user."""
        return self.id

    @staticmethod
    @lru_cache(maxsize=1)
    def get_by_id(user_id: Union[str, ObjectId, Dict[Literal["$oid"], str]]) -> "LoginUser":
        """Lookup the user database ID and create a new `LoginUser`
        with the relevant metadata.

        Parameters:
            user_id: The user's ID in the database, either as a string,
                an ObjectID, or a JSON `{'$oid': <id>}` dictionary.

        Raises:
            ValueError: if the user could not be found.

        """
        if isinstance(user_id, dict):
            user_id = user_id["$oid"]

        user = flask_mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User {user_id} not found in database.")

        return LoginUser(_id=user_id, data=user)

    @property
    def display_name(self) -> Optional[str]:
        """Returns the top-level display name for the user, if set."""
        return self.person.display_name

    @property
    def identities(self) -> List[Identity]:
        """Returns the list of identities of the user."""
        return self.person.identities

    @property
    def identity_types(self) -> List[IdentityType]:
        """Returns a list of the identity types associated with the user."""
        return [identity.identity_type for identity in self.person.identities]

    def refresh(self) -> None:
        """Reconstruct the user object from their database entry, to be used when,
        e.g., a new identity has been associated with them.

        """
        self.person = self.get_by_id(self.id).person


LOGIN_MANAGER: LoginManager = LoginManager()
"""The global login manager for the app."""


@LOGIN_MANAGER.user_loader
def load_user(user_id) -> LoginUser:
    """Looks up the currently authenticated user and returns a `LoginUser` model."""
    return LoginUser.get_by_id(user_id)
