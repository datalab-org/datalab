import datetime
import subprocess as sp
import time
from pathlib import Path

import pytest

from pydatalab.config import CONFIG, RemoteFilesystem
from pydatalab.remote_filesystems import (
    get_directory_structure,
    get_directory_structures,
)

"""The Unix `tree` utility is required for many of these tests,
this variable checks whether it is installed locally."""
TREE_AVAILABLE = False
_ = sp.call("tree -v", shell=True)  # noqa: S602,S607
if _ == 0:
    TREE_AVAILABLE = True


@pytest.mark.skipif(not TREE_AVAILABLE, reason="`tree` utility not installed locally")
def test_get_directory_structure_local(random_string):
    """Check that the file directory cache is used on the second
    attempt to query a directory.

    """
    dir_name = random_string
    test_dir = RemoteFilesystem(**{"path": Path(__file__).parent.parent, "name": dir_name})
    dir_structure = get_directory_structure(test_dir)
    dir_structure.pop("last_updated")
    assert dir_structure
    assert dir_structure.pop("status") == "updated"
    assert all(k in dir_structure for k in ("type", "name", "contents"))
    assert all(k in dir_structure["contents"][0] for k in ("type", "name", "size", "time"))
    dir_structure_cached = get_directory_structure(test_dir)
    last_updated_cached = dir_structure_cached.pop("last_updated")
    assert dir_structure_cached.pop("status") == "cached"
    assert dir_structure_cached == dir_structure
    assert last_updated_cached

    # This should hit the cache again, with no update in the last modified time
    dir_structure_cached_again = get_directory_structures([test_dir])[0]
    last_updated_cached_again = dir_structure_cached_again.pop("last_updated")
    assert last_updated_cached == last_updated_cached_again
    assert dir_structure_cached_again.pop("status") == "cached"

    # Hit the cache one more time, this time requesting invalidationg (but we should be
    # below the minimum cache age)
    dir_structure_cached_again = get_directory_structures([test_dir], invalidate_cache=True)[0]
    last_updated_cached_again = dir_structure_cached_again.pop("last_updated")
    assert dir_structure_cached_again.pop("status") == "cached"
    assert last_updated_cached == last_updated_cached_again

    try:
        # Set the minimum cache age to 0 and make sure that this does indeed invalidate the cache
        # Need to sleep to allow microsecond precision differences
        CONFIG.REMOTE_CACHE_MIN_AGE = 0
        time.sleep(1)
        dir_structure_cached_again = get_directory_structure(test_dir, invalidate_cache=True)
        last_updated_cached_again = dir_structure_cached_again.pop("last_updated")
        assert last_updated_cached != last_updated_cached_again

        # Test that the cache is not invalidated when requested, even if it is out of date
        CONFIG.REMOTE_CACHE_MAX_AGE = 0
        dir_structure_cached_final = get_directory_structure(test_dir, invalidate_cache=False)
        last_updated_cached_final = dir_structure_cached_final.pop("last_updated")
        assert last_updated_cached_final == last_updated_cached_again
    finally:
        # order of these statements matter as each individual reset will be validated
        CONFIG.REMOTE_CACHE_MAX_AGE = 60
        CONFIG.REMOTE_CACHE_MIN_AGE = 1

    assert get_directory_structures([], invalidate_cache=True) == []


@pytest.mark.skipif(not TREE_AVAILABLE, reason="`tree` utility not installed locally")
def test_get_missing_directory_structure_local(random_string):
    """Check that missing directories do not crash everything, and that
    they still get cached.
    """
    dir_name = random_string
    test_dir = RemoteFilesystem(**{"path": "this_directory_does_not_exist", "name": dir_name})
    dir_structure = get_directory_structure(test_dir)
    assert dir_structure
    assert all(k in dir_structure for k in ("type", "name", "contents"))
    dir_structure_cached = get_directory_structure(test_dir)
    last_updated_cached = dir_structure_cached.pop("last_updated")
    dir_structure.pop("last_updated")
    assert dir_structure_cached == dir_structure
    assert last_updated_cached


@pytest.mark.skipif(not TREE_AVAILABLE, reason="`tree` utility not installed locally")
def test_get_directory_structure_remote(real_mongo_client, random_string):
    """Check that a fake ssh server initially fails, then successfully returns
    once the cache has been mocked.

    """
    dir_name = random_string
    test_dir = RemoteFilesystem(
        **{"name": dir_name, "hostname": "ssh://fake.host", "path": Path(__file__).parent.parent}
    )
    dir_structure = get_directory_structure(test_dir)
    assert dir_structure["contents"][0]["type"] == "error"
    dummy_dir_structure = {
        "contents": [],
        "name": "test",
        "last_updated": datetime.datetime.now(tz=datetime.timezone.utc),
        "type": "toplevel",
    }
    real_mongo_client.get_database().remoteFilesystems.insert_one(dummy_dir_structure)
    dir_structure = get_directory_structure(test_dir)
    assert dir_structure["last_updated"]


def test_scp_escape_spaces():
    """Test whether the escaping function for scp paths works correctly
    in edge cases: already-escaped spaces, mixtures etc."""
    from pydatalab.file_utils import _escape_spaces_scp_path

    assert (
        _escape_spaces_scp_path(r"ssh://host:path with spaces")
        == r'ssh://host:"path\ with\ spaces"'
    )
    assert (
        _escape_spaces_scp_path(r"ssh://host:path with spaces/in two places/")
        == r'ssh://host:"path\ with\ spaces/in\ two\ places/"'
    )
    assert (
        _escape_spaces_scp_path(
            r"ssh://host:path with spaces/in two places/with\ some already\ escaped"
        )
        == r'ssh://host:"path\ with\ spaces/in\ two\ places/with\ some\ already\ escaped"'
    )
    assert (
        _escape_spaces_scp_path(r"ssh://host:path_without_spaces")
        == r"ssh://host:path_without_spaces"
    )
