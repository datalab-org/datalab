from pathlib import Path
from typing import Dict, List, Union

from pydantic import BaseSettings, Field, root_validator

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
    {
        "name": "bob/James_Steele",
        "hostname": "ssh://diskhost-c.ch.private.cam.ac.uk",
        "path": "/zfs/greygroup/instruments/bob/James_Steele",
    },
    {
        "name": "Diamond Light Source/i11/cy28349-9",
        "hostname": "ssh://ssh.diamond.ac.uk",
        "path": "/dls/i11/data/2022/cy30731-1",
    },
    {
        "name": "Empyrean XRD/2022/jmas5",
        "hostname": "ssh://analytical-data-fs.ch.private.cam.ac.uk",
        "path": r"/data/group/analytical-data/general/shares/xray/PXRD/Empyrean\ XRD\ -\ Service\ Data/2022/Grey/JMAS5",
    },

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
