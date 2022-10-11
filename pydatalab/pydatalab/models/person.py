from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from pydatalab.models.entries import Entry


class IdentityType(str, Enum):

    EMAIL = "email"
    ORCID = "orcid"
    GITHUB = "github"


class Identity(BaseModel):

    identity_type: IdentityType = Field(description="The type or provider of the identity.")
    identifier: str = Field(
        description="The identifier for the identity, e.g., an email address, an ORCID, a GitHub user ID."
    )
    name: Optional[str] = Field(
        description="The name associated with the identity, e.g., an institutional username, a GitHub username."
    )
    verified: bool = Field(description="Whether the identity has been verified.")


class Person(Entry):

    type: str = Field("people", const=True)

    orcid: Optional[str] = Field(None)

    affiliation: Optional[str] = Field(None)

    family_names: Optional[str] = Field(None)

    published_name: Optional[str] = Field(None)

    contact_email: EmailStr = Field(None)

    identities: List[Identity] = Field(None)
