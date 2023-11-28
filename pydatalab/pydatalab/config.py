import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import (
    AnyUrl,
    BaseModel,
    BaseSettings,
    Field,
    ValidationError,
    root_validator,
    validator,
)

from pydatalab.models import Person
from pydatalab.models.utils import RandomAlphabeticalRefcodeFactory, RefCodeFactory

__all__ = ("CONFIG", "ServerConfig", "DeploymentMetadata", "RemoteFilesystem")


def config_file_settings(settings: BaseSettings) -> Dict[str, Any]:
    """Returns a dictionary of server settings loaded from the default or specified
    JSON config file location (via the env var `PYDATALAB_CONFIG_FILE`).

    """
    config_file = Path(os.getenv("PYDATALAB_CONFIG_FILE", "/app/config.json"))

    res = {}
    if config_file.is_file():
        logging.debug("Loading from config file at %s", config_file)
        config_file_content = config_file.read_text(encoding=settings.__config__.env_file_encoding)

        try:
            res = json.loads(config_file_content)
        except json.JSONDecodeError as json_exc:
            raise RuntimeError(f"Unable to read JSON config file {config_file}") from json_exc

    else:
        logging.debug("Unable to load from config file at %s", config_file)
        res = {}

    return res


class DeploymentMetadata(BaseModel):
    """A model for specifying metadata about a datalab deployment."""

    maintainer: Optional[Person]
    issue_tracker: Optional[AnyUrl]
    homepage: Optional[AnyUrl]
    source_repository: Optional[AnyUrl]

    @validator("maintainer")
    def strip_fields_from_person(cls, v):
        if not v.contact_email:
            raise ValueError("Must provide contact email for maintainer.")

        return Person(contact_email=v.contact_email, display_name=v.display_name)

    class Config:
        extra = "allow"


class RemoteFilesystem(BaseModel):
    """Configuration for specifying a single remote filesystem
    accessible from the server.
    """

    name: str
    hostname: Optional[str]
    path: Path


class ServerConfig(BaseSettings):
    """A model that provides settings for deploying the API."""

    SECRET_KEY: str = Field(os.urandom(12).hex(), description="The secret key to use for Flask.")

    MONGO_URI: str = Field(
        "mongodb://localhost:27017/datalabvue",
        description="The URI for the underlying MongoDB.",
    )
    FILE_DIRECTORY: Union[str, Path] = Field(
        Path(__file__).parent.joinpath("../files").resolve(),
        description="The path under which to place stored files uploaded to the server.",
    )

    DEBUG: bool = Field(True, description="Whether to enable debug-level logging in the server.")

    TESTING: bool = Field(
        False, description="Whether to run the server in testing mode, i.e., without user auth."
    )

    IDENTIFIER_PREFIX: str = Field(
        None,
        description="The prefix to use for identifiers in this deployment, e.g., 'grey' in `grey:AAAAAA`",
    )

    REFCODE_GENERATOR: Type[RefCodeFactory] = Field(
        RandomAlphabeticalRefcodeFactory, description="The class to use to generate refcodes."
    )

    REMOTE_FILESYSTEMS: List[RemoteFilesystem] = Field(
        [],
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

    BEHIND_REVERSE_PROXY: bool = Field(
        False,
        description="Whether the Flask app is being deployed behind a reverse proxy. If `True`, the reverse proxy middleware described in the [Flask docs](https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/) will be attached to the app.",
    )

    GITHUB_ORG_ALLOW_LIST: Optional[List[str]] = Field(
        None,
        description="A list of GitHub organization IDs (not names), that the membership of which will be required to register a new datalab account.",
    )

    DEPLOYMENT_METADATA: Optional[DeploymentMetadata] = Field(
        None, description="A dictionary containing metadata to serve at `/info`."
    )

    MAX_CONTENT_LENGTH: int = Field(
        100 * 1000 * 1000,
        description=r"""Direct mapping to the equivalent Flask setting. In practice, limits the file size that can be uploaded.
Defaults to 100 GB to avoid filling the tmp directory of a server.

Warning: this value will overwrite any other values passed to `FLASK_MAX_CONTENT_LENGTH` but is included here to clarify
its importance when deploying a datalab instance.""",
    )

    @root_validator
    def validate_cache_ages(cls, values):
        if values.get("REMOTE_CACHE_MIN_AGE") > values.get("REMOTE_CACHE_MAX_AGE"):
            raise RuntimeError(
                f"The maximum cache age must be greater than the minimum cache age: min {values.get('REMOTE_CACHE_MIN_AGE')=}, max {values.get('REMOTE_CACHE_MAX_AGE')=}"
            )
        return values

    @validator("IDENTIFIER_PREFIX", pre=True, always=True)
    def validate_identifier_prefix(cls, v, values):
        """Make sure that the identifier prefix is set and is valid, raising clear error messages if not.

        If in testing mode, then set the prefix to test too.

        """

        if values.get("TESTING"):
            return "test"

        if v is None:
            import warnings

            warning_msg = (
                "You should configure an identifier prefix for this deployment. "
                "You should attempt to make it unique to your deployment or group. "
                "In the future these will be optionally globally validated versus all deployments for uniqueness. "
                "For now the value of `test` will be used."
            )

            warnings.warn(warning_msg)
            logging.warning(warning_msg)

            return "test"

        if len(v) > 12:
            raise RuntimeError(
                "Identifier prefix must be less than 12 characters long, received {v=}"
            )

        # test a trial refcode
        from pydatalab.models.utils import Refcode

        try:
            Refcode(f"{v}:AAAAAA")
        except ValidationError as exc:
            raise RuntimeError(
                f"Invalid identifier prefix: {v}. Validation with refcode `AAAAAA` returned error: {exc}"
            )

        return v

    class Config:
        env_prefix = "pydatalab_"
        extra = "allow"
        env_file_encoding = "utf-8"
        validate_assignment = True

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (init_settings, env_settings, config_file_settings, file_secret_settings)

    def update(self, mapping):
        for key in mapping:
            setattr(self, key.upper(), mapping[key])


CONFIG: ServerConfig = ServerConfig()
"""The global server configuration object.
This is a singleton instance of the `ServerConfig` model.
"""
