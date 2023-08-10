from pathlib import Path

import pytest

from pydatalab.config import CONFIG


@pytest.fixture(scope="module", name="default_filepath")
def fixture_default_filepath():
    return Path(__file__).parent.joinpath(
        "../../example_data/echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
    )


@pytest.fixture(scope="module", name="insert_default_sample")
def fixture_insert_default_sample(client, default_sample):  # pylint: disable=unused-argument
    from pydatalab.mongo import flask_mongo

    flask_mongo.db.items.insert_one(default_sample.dict(exclude_unset=False))
    yield
    flask_mongo.db.items.delete_one({"item_id": default_sample.item_id})


@pytest.mark.dependency()
def test_upload(
    client, default_filepath, insert_default_sample, default_sample
):  # pylint: disable=unused-argument
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
    assert response.json["status"], "success"
    assert response.status_code == 201


@pytest.mark.dependency(depends=["test_upload"])
def test_get_file_and_delete(client, default_filepath, default_sample):
    response = client.get(f"/get-item-data/{default_sample.item_id}")
    assert response.json["status"] == "success"
    assert response.status_code == 200

    assert "files_data" in response.json
    assert len(response.json["files_data"]) == 1
    file_id = [_id for _id in response.json["files_data"]][0]

    assert "item_data" in response.json
    assert file_id in response.json["item_data"]["file_ObjectIds"]

    assert (
        response.json["files_data"][file_id]["location"]
        == f"{CONFIG.FILE_DIRECTORY}/{file_id}/{default_filepath.name}"
    )
    assert response.json["files_data"][file_id]["name"] == default_filepath.name
    assert response.json["files_data"][file_id]["size"] == 2465718

    file_response = client.get(f"/files/{file_id}/{default_filepath.name}")
    assert file_response.json is None
    assert file_response.status_code == 200
    assert len(file_response.data) == 2465718

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
    assert not response.json["files_data"]
