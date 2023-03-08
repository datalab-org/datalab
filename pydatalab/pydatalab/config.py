import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import AnyUrl, BaseModel, BaseSettings, Field, root_validator, validator

from pydatalab.models import Person
from pydatalab.models.utils import RandomAlphabeticalRefcodeFactory, RefCodeFactory


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


class ServerConfig(BaseSettings):
    """A model that provides settings for deploying the API."""

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

    TESTING: bool = Field(
        False, description="Whether to run the server in testing mode, i.e., without user auth."
    )

    IDENTIFIER_PREFIX: str = Field(
        "grey",
        description="The prefix to use for identifiers in this deployment, e.g., `grey:AAAAAA`",
    )

    REFCODE_GENERATOR: Type[RefCodeFactory] = Field(
        RandomAlphabeticalRefcodeFactory, description="The class to use to generate refcodes."
    )

    REMOTE_FILESYSTEMS: List[Dict[str, str]] = Field(
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
        description="Whether the Flask app is being deployed behind a reverse proxy. If `True`, the reverse proxy middleware described in the Flask docs (https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/) will be attached to the app.",
    )

    GITHUB_ORG_ALLOW_LIST: Optional[List[str]] = Field(
        None,
        description="A list of GitHub organization IDs (not names), that the membership of which will be required to register a new datalab account.",
    )

    DEPLOYMENT_METADATA: Optional[DeploymentMetadata] = Field(
        None, description="A dictionary containing metadata to serve at `/info`."
    )

    @root_validator
    def validate_cache_ages(cls, values):
        if values.get("REMOTE_CACHE_MIN_AGE") > values.get("REMOTE_CACHE_MAX_AGE"):
            raise RuntimeError(
                f"The maximum cache age must be greater than the minimum cache age: {values}"
            )
        return values

    class Config:
        env_prefix = "pydatalab_"
        extra = "allow"
        env_file_encoding = "utf-8"

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


CONFIG = ServerConfig()


def log_config():
    """Adds the current server configuration to the log."""
    from pydatalab.logger import LOGGER

    LOGGER.info("Loaded config with options: %s", CONFIG.dict())


log_config()
