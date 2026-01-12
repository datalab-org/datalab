from __future__ import annotations

from enum import Enum

import bson
import bson.errors
from pydantic import BaseModel, ConstrainedStr, Field, parse_obj_as, validator
from pydantic import EmailStr as PydanticEmailStr

from pydatalab.models.entries import Entry
from pydatalab.models.utils import HumanReadableIdentifier, PyObjectId, UserRole


class IdentityType(str, Enum):
    """A string enum representing the supported verifiable identity types."""

    EMAIL = "email"
    ORCID = "orcid"
    GITHUB = "github"


class Identity(BaseModel):
    """A model for identities that can be provided by external systems
    and associated with a given user.

    """

    identity_type: IdentityType
    """The type or provider of the identity."""

    identifier: str
    """The identifier for the identity, e.g., an email address, an ORCID, a GitHub user ID."""

    name: str
    """The name associated with the identity to be exposed in free-text searches over people, e.g., an institutional username, a GitHub username."""

    verified: bool = Field(False)
    """Whether the identity has been verified (by some means, e.g., OAuth2 or email)"""

    display_name: str | None
    """The user's display name associated with the identity, also to be exposed in free text searches."""

    @validator("name", pre=True, always=True)
    def add_missing_name(cls, v, values):
        """If the identity is created without a free-text 'name', then
        for certain providers, populate this field so that it can appear
        in the free text index, e.g., an ORCID, or an institutional username
        from an email address.

        """
        if v is None:
            if values["identity_type"] == IdentityType.ORCID:
                return values["identifier"]
            if values["identity_type"] == IdentityType.EMAIL:
                return values["identifier"].split("@")[0]

        return v

    @validator("verified", pre=True, always=True)
    def add_missing_verification(cls, v):
        """Fills in missing value for `verified` if not given."""
        if not v:
            v = False
        return v


class DisplayName(ConstrainedStr):
    """A constrained string less than 150 characters long but with
    non-empty content, intended to be entered by the user.

    """

    max_length = 150
    min_length = 1
    strip_whitespace = True

    def __new__(cls, value):
        return parse_obj_as(cls, value)


class EmailStr(PydanticEmailStr):
    """A constrained string that represents a valid email address,
    using pydantic's EmailStr type but with validators accesible outside
    of models for partial validation.

    """

    max_length = 1000

    def __new__(cls, value):
        return cls.validate(value)


class AccountStatus(str, Enum):
    """A string enum representing the account status."""

    ACTIVE = "active"
    UNVERIFIED = "unverified"
    DEACTIVATED = "deactivated"


class Group(Entry):
    """A model that describes a group of users, for the sake
    of applying group permissions.

    Each `Person` can point to multiple groups.

    Relationships between groups can be described via the `relationships`
    field inherited from `Entry`.

    """

    type: str = Field("groups", const=True)
    """The entry type as a string."""

    group_id: HumanReadableIdentifier | None = Field(None)
    """A short, locally-unique ID for the group."""

    members: list[dict] = Field(None)
    """A list of people that belong to this group."""

    display_name: DisplayName | None = Field(None)
    """The chosen display name for the group"""

    description: str | None = Field(None)
    """A description of the group"""

    managers: list[PyObjectId | dict] = Field(default_factory=list)
    """A list of user IDs that can manage this group."""

    @validator("members", pre=True, always=True)
    def cast_members_to_people(cls, v):
        """Casts members to list of people if not None."""
        if v is not None:
            return [Person(**member).dict(exclude_unset=True) for member in v]

        return v

    @validator("managers", pre=True, always=True)
    def cast_managers_to_people(cls, v):
        """Casts managers to list of people if not None."""
        if v and isinstance(v[0], dict):
            return [
                Person(**member).dict(exclude_unset=True)
                for member in v
                if isinstance(member, dict)
            ]

        return v


class Person(Entry):
    """A model that describes an individual and their digital identities."""

    type: str = Field("people", const=True)
    """The entry type as a string."""

    identities: list[Identity] = Field(default_factory=list)
    """A list of identities attached to this person, e.g., email addresses, OAuth accounts."""

    display_name: DisplayName | None = Field(None)
    """The user-chosen display name."""

    contact_email: EmailStr | None = Field(None)
    """In the case of multiple *verified* email identities, this email will be used as the primary contact."""

    managers: list[PyObjectId] | None = Field(None)
    """A list of user IDs that can manage this person's items."""

    role: UserRole = Field(UserRole.USER)
    """The role assigned to this person."""

    groups: list[Group] | None = Field(default_factory=list)
    """A list of groups that this person belongs to."""

    account_status: AccountStatus = Field(AccountStatus.UNVERIFIED)
    """The status of the user's account."""

    @validator("type", pre=True, always=True)
    def add_missing_type(cls, v):
        """Fill in missing `type` field if not provided."""
        if v is None:
            v = "people"
        return v

    @validator("type", pre=True)
    def set_default_type(cls, _):
        return "people"

    @staticmethod
    def new_user_from_identity(
        identity: Identity,
        use_display_name: bool = True,
        use_contact_email: bool = True,
        account_status: AccountStatus = AccountStatus.UNVERIFIED,
    ) -> Person:
        """Create a new `Person` object with the given identity.

        Arguments:
            identity: The identity to populate the `identities` field with.
            use_display_name: Whether to set the top-level `display_name`
                field with any display name present in the identity.
            use_contact_email: If the identity provided is an email address,
                this argument decides whether to populate the top-level
                `contact_email` field with the address of this identity.
            account_status: The starting account status of the user.

        Returns:
            A `Person` object with only the provided identity.

        """
        user_id = bson.ObjectId()

        display_name = None
        if use_display_name:
            display_name = identity.display_name

        contact_email = None
        if use_contact_email and identity.identity_type is IdentityType.EMAIL:
            contact_email = identity.identifier

        return Person(
            immutable_id=user_id,
            identities=[identity],
            display_name=display_name,
            contact_email=contact_email,
            account_status=account_status,
        )
