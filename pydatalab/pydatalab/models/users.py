from typing import Set
from pydantic import BaseModel


class User(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    github_username: str
    orcid: str
    password_hash: str
    groups: Set[str]