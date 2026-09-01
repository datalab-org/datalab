from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import EmailStr as PydanticEmailStr
from pydantic import (
    Field,
    StringConstraints,
    field_validator,
)

from pydatalab.models.entries import Entry
from pydatalab.models.utils import BaseModel, HumanReadableIdentifier, PyObjectId, UserRole


class IdentityType(str, Enum):
    """A string enum representing the supported verifiable identity types."""

    EMAIL = "email"
    ORCID = "orcid"
    GITHUB = "github"
    GOOGLE = "google"
    MICROSOFT = "microsoft"


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

    verified: bool = False
    """Whether the identity has been verified (by some means, e.g., OAuth2 or email)"""

    display_name: str | None = None
    """The user's display name associated with the identity, also to be exposed in free text searches."""

    @field_validator("name", mode="before")
    @classmethod
    def add_missing_name(cls, v, info):
        """If the identity is created without a free-text 'name', then
        for certain providers, populate this field so that it can appear
        in the free text index, e.g., an ORCID, or an institutional username
        from an email address.

        """
        if v is None and hasattr(info, "data") and info.data:
            data = info.data
            if data.get("identity_type") == IdentityType.ORCID:
                return data.get("identifier")
            if data.get("identity_type") == IdentityType.EMAIL:
                identifier = data.get("identifier", "")
                return identifier.split("@")[0] if "@" in identifier else identifier
        return v

    @field_validator("verified", mode="before")
    @classmethod
    def add_missing_verification(cls, v):
        """Fills in missing value for `verified` if not given."""
        if not v:
            v = False
        return v


DisplayName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=150, strip_whitespace=True),
]
"""A constrained string less than 150 characters long but with non-empty content, intended to be entered by the user."""


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

    type: Literal["groups"] = "groups"
    """The entry type as a string."""

    group_id: HumanReadableIdentifier | None = None
    """A short, locally-unique ID for the group."""

    members: list[dict] = Field(default_factory=list)
    """A list of people that belong to this group; stored on the user objects."""

    display_name: DisplayName | None = None
    """The chosen display name for the group"""

    description: str | None = None
    """A description of the group"""

    managers: list[PyObjectId | dict] = Field(default_factory=list)
    """A list of user IDs that can manage this group; stored in db as list of IDs."""

    @field_validator("members", mode="before")
    @classmethod
    def cast_members_to_people(cls, v):
        """Casts members to list of people if not None."""
        if v is not None:
            return [Person(**member).model_dump(exclude_unset=True) for member in v]

        return v

    @field_validator("managers", mode="before")
    @classmethod
    def cast_managers_to_people(cls, v):
        """Casts managers to list of people if not None."""
        if v and isinstance(v[0], dict):
            return [
                Person(**member).model_dump(exclude_unset=True)
                for member in v
                if isinstance(member, dict)
            ]

        return v


class Person(Entry):
    """A model that describes an individual and their digital identities."""

    type: Literal["people"] = "people"
    """The entry type as a string."""

    identities: list[Identity] = Field(default_factory=list)
    """A list of identities attached to this person, e.g., email addresses, OAuth accounts."""

    display_name: DisplayName | None = Field(None)
    """The user-chosen display name."""

    contact_email: EmailStr | None = Field(None)
    """In the case of multiple *verified* email identities, this email will be used as the primary contact."""

    gravatar_hash: str | None = Field(None)
    """MD5 hash used by the frontend to fetch a Gravatar avatar without exposing the raw email."""

    managers: list[PyObjectId] | None = Field(None)
    """A list of user IDs that can manage this person's items."""

    role: UserRole = Field(UserRole.USER)
    """The role assigned to this person."""

    groups: list[Group] | None = Field(default_factory=list)
    """A list of groups that this person belongs to."""

    account_status: AccountStatus = Field(AccountStatus.UNVERIFIED)
    """The status of the user's account."""

    @field_validator("type", mode="before")
    @classmethod
    def add_missing_type(cls, v):
        """Fill in missing `type` field if not provided."""
        if v is None:
            v = "people"
        return v

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
        display_name = None
        if use_display_name:
            display_name = identity.display_name

        contact_email = None
        if use_contact_email and identity.identity_type is IdentityType.EMAIL:
            contact_email = identity.identifier

        from pydatalab.mongo import gravatar_hash_for

        return Person(
            identities=[identity],
            display_name=display_name,
            contact_email=contact_email,
            account_status=account_status,
            gravatar_hash=gravatar_hash_for(contact_email, display_name),
        )
