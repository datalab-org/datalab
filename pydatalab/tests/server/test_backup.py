"""Tests for backup creation and restoration.
Does not test backup scheduling.

"""

import shutil
import tarfile
import time

import pytest

from pydatalab.backups import create_backup
from pydatalab.config import BackupStrategy

# Check whether mongodump (and mongorestore by extension) is present; skip backup tests if not
mongodump_present = pytest.mark.skipif(
    shutil.which("mongodump") is None, reason="mongodump not installed"
)


@mongodump_present
def test_backup_creation(
    client, database, default_filepath, insert_default_sample, default_sample, tmp_path
):
    """Test whether a simple local backup can be created."""
    assert database.items.count_documents({}) == 1
    with open(default_filepath, "rb") as f:
        response = client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": default_sample.item_id,
                "file": [(f, default_filepath.name)],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )
    assert response.status_code == 201

    strategy = BackupStrategy(
        hostname=None,
        location=tmp_path,
        frequency="5 4 * * *",  # 4:05 every day
        retention=2,
    )
    create_backup(strategy)
    assert len(list(tmp_path.glob("*"))) == 1

    # make sure the next ones have a different timestamp
    time.sleep(1)
    create_backup(strategy)
    assert len(list(tmp_path.glob("*"))) == 2

    time.sleep(1)
    create_backup(strategy)
    assert len(list(tmp_path.glob("*"))) == 2

    # remove the first one and check contents of the second
    backups = list(tmp_path.glob("*"))
    backups.pop().unlink()

    backup = backups.pop()

    with tarfile.open(backup, mode="r:gz") as tar:
        members = {m.name for m in tar.getmembers()}

    assert any(m.startswith("mongodb/") for m in members)
    # Only one file is backed up but the tar file reports a "member" for the containing directory too
    assert sum(1 for m in members if m.startswith("files/")) == 2
    assert sum(1 for m in members if m.startswith("config/")) == 1
