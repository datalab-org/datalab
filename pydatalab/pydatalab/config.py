from pathlib import Path
from typing import Dict, List, Union
import os

from pydantic import BaseModel, BaseSettings, Field, root_validator

DEFAULT_REMOTES = [
    {
        "name": "bob/Josh_B",
        "hostname": "ssh://diskhost-c.ch.private.cam.ac.uk",
        "path": "/zfs/greygroup/instruments/bob/Josh_B",
    },
    {
        "name": "carlos/Jiasi_Li",
        "hostname": "ssh://diskhost-c.ch.private.cam.ac.uk",
        "path": "/zfs/greygroup/instruments/carlos/Jiasi_Li",
    },
    {
        "name": "carlos/Josh_Bocarsly",
        "hostname": "ssh://diskhost-c.ch.private.cam.ac.uk",
        "path": "/zfs/greygroup/instruments/carlos/Josh_Bocarsly",
    },
    {
        "name": "eve/Josh_Bocarsly",
        "hostname": "ssh://diskhost-c.ch.private.cam.ac.uk",
        "path": "/zfs/greygroup/instruments/eve/Josh_Bocarsly",
    },
]

class OAuthProvider(BaseModel):

    client_id: str = Field(None, description="The client ID for this datalab instance registered with the OAuth provider.")
    client_secret: str = Field(None, description="The client secret for this datalab instance registered with the OAuth provider.")
    token_url: str = Field(None, description="The provider's token URL.")
    base_url: str = Field(None, description="The provider's OAuth base URL.")
    known_users: List[str] = Field(None, description="A list of known users that will be authenticated for the API after login.")
    name: str = Field(None)


OAUTH_PROVIDERS = [
    OAuthProvider(
        client_id=os.environ.get("PYDATALAB_GITHUB_OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("PYDATALAB_GITHUB_OAUTH_CLIENT_SECRET"),
        token_url="https://github.com/login/oauth/access_token",
        base_url="https://github.com/login/oauth/authorize",
        name="github",
        known_users=["ml-evs", "jdbocarsly"]
    ),
    OAuthProvider(
        client_id=os.environ.get("PYDATALAB_ORCID_SANDBOX_OAUTH_CLIENT_ID"),
        client_secret=os.environ.get("PYDATALAB_ORCID_SANDBOX_OAUTH_CLIENT_SECRET"),
        token_url="https://sandbox.orcid.org/oauth/token?scope=/authenticate",
        base_url="https://sandbox.orcid.org/oauth/authorize?scope=/authenticate",
        name="orcid_sandbox",
        known_users=[
            "0000-0002-2903-9254" # Sandbox ID for orcid_sandbox@ml-evs.science
        ],
    )
]


class ServerConfig(BaseSettings):
    SECRET_KEY: str = Field("dummy key", description="The secret key to use for Flask.")

    MONGO_URI: str = Field(
        "mongodb://localhost:27017/datalabvue",
        description="The URI for the underlying MongoDB.",
    )

    FILE_DIRECTORY: Union[str, Path] = Field(
        Path(__file__).parent.joinpath("../files").resolve(),
        description="The path under which to place stored files uploaded to the server.",
    )

    DEBUG: bool = Field(True, description="Whether to enable debug-level logging in the server.")

    REMOTE_FILESYSTEMS: List[Dict[str, str]] = Field(
        DEFAULT_REMOTES,
        descripton="A list of dictionaries describing remote filesystems to be accessible from the server.",
    )

    REMOTE_CACHE_MAX_AGE: int = Field(
        60,
        description="The maximum age, in minutes, of the remote filesystem cache after which it should be invalidated.",
    )

    REMOTE_CACHE_MIN_AGE: int = Field(
        1,
        description="The minimum age, in minutes, of the remote filesystem cache, below which the cache will not be invalidated if an update is manually requested.",
    )

    OAUTH_PROVIDERS: Dict[str, OAuthProvider] = Field({p.name: p for p in OAUTH_PROVIDERS})

    @root_validator
    def validate_cache_ages(cls, values):
        if values.get("REMOTE_CACHE_MIN_AGE") > values.get("REMOTE_CACHE_MAX_AGE"):
            raise RuntimeError("The maximum cache age must be greater than the minimum cache age.")
        return values

    class Config:
        env_prefix = "pydatalab_"
        extra = "allow"

    def update(self, mapping):
        for key in mapping:
            setattr(self, key.upper(), mapping[key])


CONFIG = ServerConfig()

__all__ = ("CONFIG",)
