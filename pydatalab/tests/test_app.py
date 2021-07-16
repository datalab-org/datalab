import pytest

SAMPLE = {
    "sample_id": "12345",
    "name": "other_sample",
    "date": "02-01-1970",
}

from pydatalab.main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.mark.dependency()
def test_empty_samples(client):
    response = client.get("/samples/")
    assert len(response.json["samples"]) == 0

    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_empty_samples"])
def test_new_sample(client):
    response = client.post("/new-sample/", json=SAMPLE)
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in SAMPLE.keys():
        assert response.json["sample_list_entry"][key] == SAMPLE[key]

@pytest.mark.dependency(depends=["test_new_sample"])
def test_get_sample_data(client):
    response = client.get("/get_sample_data/12345")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in SAMPLE.keys():
        assert response.json["sample_data"][key] == SAMPLE[key]


@pytest.mark.dependency(depends=["test_new_sample"])
def test_new_sample_collision(client):
    # Try to do the same thing again, expecting an ID collision
    response = client.post("/new-sample/", json=SAMPLE)
    assert response.status_code == 400


@pytest.mark.dependency(depends=["test_new_sample"])
def test_save_sample(client):
    updated_sample = SAMPLE.copy()
    updated_sample.update({"description": "This is a newer test sample."})
    response = client.post(
        "/save-sample/",
        json={"sample_id": SAMPLE["sample_id"], "data": updated_sample}
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = client.get("/get_sample_data/12345")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    for key in SAMPLE.keys():
        assert response.json[key] == updated_sample[key]


@pytest.mark.dependency(depends=["test_new_sample"])
def test_delete_sample(client):
    response = client.get(
        f"/delete-sample/{SAMPLE['sample_id']}",
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # Check it was actually deleted
    response = client.get(
        f"/get_sample_data/{SAMPLE['sample_id']}",
    )
    assert response.status_code == 404
    assert response.json["status"] == "error"
