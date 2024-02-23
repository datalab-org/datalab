from pathlib import Path

import pytest

from pydatalab.config import ServerConfig, SMTPSettings
from pydatalab.main import create_app


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


def test_config_override():
    app = create_app(
        config_override={"REMOTE_FILESYSTEMS": [{"hostname": None, "path": "/", "name": "local"}]}
    )
    assert app.config["REMOTE_FILESYSTEMS"][0]["hostname"] is None
    assert app.config["REMOTE_FILESYSTEMS"][0]["path"] == Path("/")

    from pydatalab.config import CONFIG

    assert CONFIG.REMOTE_FILESYSTEMS[0].hostname is None
    assert CONFIG.REMOTE_FILESYSTEMS[0].path == Path("/")


def test_validators():
    # check bad prefix
    with pytest.raises(
        RuntimeError, match="Identifier prefix must be less than 12 characters long,"
    ):
        _ = ServerConfig(IDENTIFIER_PREFIX="this prefix is way way too long", TESTING=False)


def test_mail_settings_combinations(tmpdir):
    """Tests that the config file mail settings get passed
    correctly to the flask settings, and that additional
    overrides can be provided as environment variables.
    """

    from pydatalab.config import CONFIG

    CONFIG.update(
        {
            "EMAIL_AUTH_SMTP_SETTINGS": SMTPSettings(
                MAIL_SERVER="example.com",
                MAIL_DEFAULT_SENDER="test@example.com",
                MAIL_PORT=587,
                MAIL_USE_TLS=True,
                MAIL_USERNAME="user",
            )
        }
    )

    app = create_app()
    assert app.config["MAIL_SERVER"] == "example.com"
    assert app.config["MAIL_DEFAULT_SENDER"] == "test@example.com"
    assert app.config["MAIL_PORT"] == 587
    assert app.config["MAIL_USE_TLS"] is True
    assert app.config["MAIL_USERNAME"] == "user"

    # write temporary .env file and check that it overrides the config
    env_file = Path(tmpdir.join(".env"))
    env_file.write_text("MAIL_PASSWORD=password\nMAIL_DEFAULT_SENDER=test2@example.com")

    app = create_app(env_file=env_file)
    assert app.config["MAIL_PASSWORD"] == "password"
    assert app.config["MAIL_DEFAULT_SENDER"] == "test2@example.com"
