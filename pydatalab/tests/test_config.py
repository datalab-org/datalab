from pathlib import Path

import pytest


def test_default_settings():
    from pydatalab.config import ServerConfig

    config = ServerConfig()
    assert config.MONGO_URI == "mongodb://localhost:27017/datalabvue"
    assert config.SECRET_KEY
    assert Path(config.FILE_DIRECTORY).name == "files"


def test_update_settings():
    from pydatalab.config import ServerConfig

    config = ServerConfig()
    new_settings = {
        "mongo_uri": "mongodb://test",
        "new_key": "some new data",
    }
    config.update(new_settings)

    assert new_settings["mongo_uri"] == config.MONGO_URI
    assert new_settings["new_key"] == config.NEW_KEY
    assert config.SECRET_KEY
    assert Path(config.FILE_DIRECTORY).name == "files"


def test_config_override():
    from pydatalab.main import create_app

    app = create_app(
        config_override={"REMOTE_FILESYSTEMS": [{"hostname": None, "path": "/", "name": "local"}]}
    )
    assert app.config["REMOTE_FILESYSTEMS"][0]["hostname"] is None
    assert app.config["REMOTE_FILESYSTEMS"][0]["path"] == Path("/")

    from pydatalab.config import CONFIG

    assert CONFIG.REMOTE_FILESYSTEMS[0].hostname is None
    assert CONFIG.REMOTE_FILESYSTEMS[0].path == Path("/")


def test_env_var_flask_config_override(secret_key):
    """Temporarily set an environment variable and check that it gets
    passed to the flask config correctly. Also make sure that the datalab
    secret key is preferred over the env var.
    """
    with pytest.MonkeyPatch.context() as m:
        from pydatalab.main import create_app

        m.setenv("FLASK_MAIL_PASSWORD_MOCK", "env_password")
        m.setenv("FLASK_SECRET_KEY", "too-short")
        app = create_app()
        assert app.config["MAIL_PASSWORD_MOCK"] == "env_password"  # noqa: S105
        assert app.config["SECRET_KEY"] == secret_key  # noqa: S105


def test_validators():
    from pydatalab.config import ServerConfig

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

    from pydatalab.config import CONFIG, SMTPSettings
    from pydatalab.main import create_app

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
    assert app.config["MAIL_PASSWORD"] == "password"  # noqa: S105
    assert app.config["MAIL_DEFAULT_SENDER"] == "test2@example.com"


def test_key_strength_checker():
    from pydatalab.feature_flags import _check_key_strength
    from pydatalab.main import create_app

    with pytest.raises(RuntimeError, match="Shannon entropy"):
        create_app({"SECRET_KEY": "short"})

    with pytest.raises(RuntimeError, match="Shannon entropy"):
        assert _check_key_strength("a" * 32)

    with pytest.raises(RuntimeError, match="Shannon entropy"):
        assert _check_key_strength("ab" * 16)

    assert _check_key_strength("abcdefghijklmnopqrstuvwxyz") is None
