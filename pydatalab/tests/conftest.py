import hashlib
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope="session")
def secret_key():
    """Fixture to provide a secret key for testing purposes."""
    return hashlib.sha512(b"test").hexdigest()


@pytest.fixture(scope="session", autouse=True)
def override_environment_variables(monkeypatch_session, secret_key):
    """Override the secret key and other environment variables that will
    otherwise fallover outside of testing mode.

    """
    monkeypatch_session.setenv("PYDATALAB_SECRET_KEY", secret_key)


@pytest.fixture(scope="session")
def example_data_dir():
    return Path(__file__).parent.parent / "example_data"


@pytest.fixture(scope="session", name="default_filepath")
def fixture_default_filepath(example_data_dir):
    return example_data_dir / "echem" / "jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
