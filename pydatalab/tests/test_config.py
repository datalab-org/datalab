from pathlib import Path

from pydatalab.config import CONFIG


def test_default_settings():
    assert CONFIG.SECRET_KEY == "dummy key"
    assert CONFIG.MONGO_URI == "mongodb://localhost:27017/datalabvue"
    assert Path(CONFIG.FILE_DIRECTORY).name == "files"


def test_update_settings():
    new_settings = {
        "secret_key": "new_secret",
        "mongo_uri": "mongodb://test",
        "new_key": "some new data",
    }
    CONFIG.update(new_settings)

    assert CONFIG.SECRET_KEY == new_settings["secret_key"]
    assert CONFIG.MONGO_URI == new_settings["mongo_uri"]
    assert CONFIG.NEW_KEY == new_settings["new_key"]
    assert Path(CONFIG.FILE_DIRECTORY).name == "files"
