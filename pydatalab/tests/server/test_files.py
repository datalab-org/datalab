import shutil

import pytest

from pydatalab.config import CONFIG


def test_too_large_upload(client, tmpdir, insert_default_sample, default_sample):  # pylint: disable=unused-argument
    """Test that an artificially large file upload is rejected (413)
    when it exceeds the test file size (currently 10 MB).

    """
    fname = "file_larger_than_10MB"
    path = tmpdir / fname
    path.write("0" * 11_000_000)
    with open(path, "rb") as f:
        response = client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": default_sample.item_id,
                "file": [(f, fname)],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )
    assert response.status_code == 413
    assert response.json["status"] == "error"
    assert response.json["title"] == "RequestEntityTooLarge"
    assert (
        response.json["message"]
        == "Uploaded file is too large.\nThe maximum file size is 0.01 GB.\nContact your datalab administrator if you need to upload larger files."
    )


@pytest.mark.dependency()
def test_upload(client, default_filepath, insert_default_sample, default_sample):  # pylint: disable=unused-argument
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
    assert isinstance(response.json["file_id"], str)
    assert response.json["file_information"]
    assert response.json["status"] == "success"
    assert response.status_code == 201


@pytest.mark.dependency(depends=["test_upload"])
def test_get_file_and_delete(client, default_filepath, default_sample):
    response = client.get(f"/get-item-data/{default_sample.item_id}")
    assert response.json["status"] == "success"
    assert response.status_code == 200

    assert "files" in response.json["item_data"]
    assert len(response.json["item_data"]["files"]) == 1
    file_id = [f["immutable_id"] for f in response.json["item_data"]["files"]][0]

    assert "item_data" in response.json
    assert file_id in response.json["item_data"]["file_ObjectIds"]

    assert (
        response.json["item_data"]["files"][0]["location"]
        == f"{CONFIG.FILE_DIRECTORY}/{file_id}/{default_filepath.name}"
    )
    assert response.json["item_data"]["files"][0]["name"] == default_filepath.name
    assert response.json["item_data"]["files"][0]["size"] == 2465718

    file_response = client.get(f"/files/{file_id}/{default_filepath.name}")
    assert file_response.json is None
    assert file_response.status_code == 200
    assert len(file_response.data) == 2465718
    file_response.close()

    delete_response = client.post(
        "/delete-file-from-sample/",
        json={
            "item_id": default_sample.item_id,
            "file_id": file_id,
        },
    )
    assert delete_response.json["status"] == "success"
    assert delete_response.status_code == 200

    response = client.get(f"/get-item-data/{default_sample.item_id}")
    assert response.json["status"] == "success"
    assert response.status_code == 200
    assert not response.json["item_data"]["file_ObjectIds"]
    assert not response.json["item_data"]["files"]


@pytest.mark.dependency(depends=["test_get_file_and_delete"])
def test_upload_new_version(
    client, default_filepath, insert_default_sample, default_sample, tmpdir
):  # pylint: disable=unused-argument
    """Upload a file, then upload a new version of the same file."""
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

    file_id = response.json["file_id"]
    assert file_id
    assert response.json["file_information"]
    assert response.json["status"] == "success"
    assert response.status_code == 201

    # Copy the file to a new temp directory so its fs metadata changes
    tmp_filepath = tmpdir / default_filepath.name
    shutil.copy(default_filepath, tmp_filepath)

    with open(tmp_filepath, "rb") as f:
        response_reup = client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": default_sample.item_id,
                "file": [(f, default_filepath.name)],
                "type": "application/octet-stream",
                "replace_file": file_id,
                "relativePath": "null",
            },
        )
    assert isinstance(response_reup.json["file_id"], str)
    assert response_reup.json["file_information"]
    assert response_reup.json["status"] == "success"
    assert response_reup.status_code == 201
    assert (
        response_reup.json["file_information"]["location"]
        == response.json["file_information"]["location"]
    )
    assert response_reup.json["file_id"] == response.json["file_id"]


@pytest.mark.dependency(depends=["test_upload_new_version"])
def test_file_permissions(
    client,
    another_client,
    another_user_id,
    group_id,
    default_filepath,
    insert_default_cell,
    default_cell,
    tmpdir,
):  # pylint: disable=unused-argument
    """Upload a file as one user, then test access as two different users."""
    filename = "my_secret_file.txt"
    with open(default_filepath, "rb") as f:
        response = client.post(
            "/upload-file/",
            buffered=True,
            content_type="multipart/form-data",
            data={
                "item_id": default_cell.item_id,
                "file": [(f, filename)],
                "type": "application/octet-stream",
                "replace_file": "null",
                "relativePath": "null",
            },
        )

    assert response.status_code == 201
    resp_json = response.json
    assert resp_json["status"] == "success"
    file_id = resp_json["file_id"]

    # Test that a random user cannot access the file directly
    response = another_client.get(f"/files/{file_id}/{filename}")
    assert response.status_code == 401
    assert response.json["status"] == "error"

    # Give the user access to the item, then check again
    # First get refcode for item ID
    response = client.get(f"/get-item-data/{default_cell.item_id}")
    refcode = response.json["item_data"]["refcode"]

    # Add normal user to the item
    response = client.patch(
        f"/items/{refcode}/permissions", json={"creators": [{"immutable_id": str(another_user_id)}]}
    )

    # Now check they have access to the file
    response = another_client.get(f"/files/{file_id}/{filename}")
    assert response.status_code == 200

    # Now remove them, but add their group
    response = client.patch(
        f"/items/{refcode}/permissions",
        json={"creators": [], "groups": [{"immutable_id": group_id}]},
    )

    # Now check they still have access to the file
    response = another_client.get(f"/files/{file_id}/{filename}")
    assert response.status_code == 200
