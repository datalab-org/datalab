"""Tests for backup creation and restoration.
Does not test backup scheduling.

"""
import shutil

import pytest

from pydatalab.backups import create_backup
from pydatalab.config import BackupStrategy

mongodump_present = pytest.mark.skipif(
    shutil.which("mongodump") is None, reason="mongodump not installed"
)


@mongodump_present
def test_backup_creation(
    client, database, default_filepath, insert_default_sample, default_sample, tmpdir
):
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
        location=tmpdir,
        frequency="5 4 * * *",  # 4:05 every day
        retention=2,
    )
    create_backup(strategy)

    assert len(tmpdir.glob("*")) == 1
    create_backup(strategy)
    assert len(tmpdir.glob("*")) == 2
    create_backup(strategy)
    assert len(tmpdir.glob("*")) == 2


@mongodump_present
def test_backup_restoration(app, client, database):
    assert database.items.count_documents({}) == 0
