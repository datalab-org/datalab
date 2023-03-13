from pathlib import Path

from pydatalab.config import ServerConfig


def test_default_settings():
    config = ServerConfig()
    assert config.MONGO_URI == "mongodb://localhost:27017/datalabvue"
    assert config.SECRET_KEY
    assert Path(config.FILE_DIRECTORY).name == "files"


def test_update_settings():
    config = ServerConfig()
    new_settings = {
        "mongo_uri": "mongodb://test",
        "new_key": "some new data",
    }
    config.update(new_settings)

    assert config.MONGO_URI == new_settings["mongo_uri"]
    assert config.NEW_KEY == new_settings["new_key"]
    assert config.SECRET_KEY
    assert Path(config.FILE_DIRECTORY).name == "files"
