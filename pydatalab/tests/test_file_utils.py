import pytest

from pydatalab.config import CONFIG
from pydatalab.file_utils import get_space_available_bytes


def test_get_space_available_bytes(tmp_path, monkeypatch):
    """The free space of a real directory should be a positive integer on any platform."""
    monkeypatch.setattr(CONFIG, "FILE_DIRECTORY", tmp_path)
    space = get_space_available_bytes()
    assert isinstance(space, int)
    assert space > 0


def test_get_space_available_bytes_uninitialised(tmp_path, monkeypatch):
    """A missing file directory should be reported as a configuration problem."""
    monkeypatch.setattr(CONFIG, "FILE_DIRECTORY", tmp_path / "definitely-not-here")
    with pytest.raises(RuntimeError):
        get_space_available_bytes()
