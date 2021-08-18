from pathlib import Path
from typing import Union

from pydantic import BaseSettings, Field


class ServerConfig(BaseSettings):
    SECRET_KEY: str = Field("dummy key", description="The secret key to use for Flask.")

    MONGO_URI: str = Field(
        "mongodb://localhost:27017/datalabvue", description="The URI for the underlying MongoDB."
    )

    UPLOAD_PATH: Union[str, Path] = Field(
        "uploads", description="The path under which to place files uploaded to the server."
    )

    FILE_DIRECTORY: Union[str, Path] = Field(
        Path(__file__).parent.joinpath("../files").resolve(),
        description="The path under which to place stored files uploaded to the server.",
    )

    DEBUG: bool = Field(False, description="Whether to enable debug-level logging in the server.")

    class Config:
        env_prefix = "pydatalab_"
        extra = "allow"

    def update(self, mapping):
        for key in mapping:
            setattr(self, key.upper(), mapping[key])


CONFIG = ServerConfig()
