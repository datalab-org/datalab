import datetime

from pydantic import BaseModel

from pydatalab.models.utils import PyObjectId


class Key(BaseModel):
    user: PyObjectId
    """id that the object belongs to"""

    created_at: "datetime.datetime"
    """date that the object was created"""

    expires_at: "datetime.datetime|None"
    """date that the object expires"""

    version: int
    """version of the key"""


class AccessToken(Key):
    refcode: str
    """The reference code of the access key"""

    active: bool
    """whether the access key is active"""

    type: str = "access_token"
    """the type of access key"""

    token: str
    """The hash of the access token"""


class ApiKey(Key):
    name: str
    """The name of the API key"""

    digest: str
    """The hash of the API key"""

    type: str = "api_key"
    """The type of the API key"""

    hash: str
    """The hash of the token"""
