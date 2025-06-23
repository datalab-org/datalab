import pytest


@pytest.mark.dependency()
def test_directories_list(client, unauthenticated_client, unverified_client, deactivated_client):
    response = client.get("/list-remote-directories")
    assert response.json
    toplevel = response.json["data"][0]
    assert toplevel["type"] == "toplevel"
    assert toplevel["status"] == "updated"

    response = unauthenticated_client.get("/list-remote-directories")
    assert response.status_code == 401
    response = unverified_client.get("/list-remote-directories")
    assert response.status_code == 401
    response = deactivated_client.get("/list-remote-directories")
    assert response.status_code == 401

    response = client.get("/remotes")
    assert response.json
    toplevel = response.json["data"][0]
    assert toplevel["type"] == "toplevel"
    assert toplevel["status"] == "cached"

    response = unauthenticated_client.get("/remotes")
    assert response.status_code == 401
    response = unverified_client.get("/remotes")
    assert response.status_code == 401
    response = deactivated_client.get("/remotes")
    assert response.status_code == 401


@pytest.mark.dependency(depends=["test_directories_list"])
def test_single_directory(client):
    response = client.get("/remotes/example_data?invalidate_cache=1")
    assert response.json
    toplevel = response.json["data"]
    assert toplevel["type"] == "toplevel"
    # even though `invalidate_cache` is set to 1, the directory is cached
    # because it was just updated in the previous test and the min age is 1
    assert toplevel["status"] == "cached"

    response = client.get("/remotes/example/data?invalidate_cache=0")
    assert response.json
    toplevel = response.json["data"]
    assert toplevel["type"] == "toplevel"
    assert toplevel["status"] == "cached"
