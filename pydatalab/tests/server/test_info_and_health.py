import os

import pytest


@pytest.mark.parametrize("url_prefix", ["", "/v0", "/v0.1", "/v0.1.0"])
def test_info_endpoint(client, url_prefix):
    response = client.get(f"{url_prefix}/info")
    assert response.status_code == 200
    assert all(k in response.json for k in ("data", "meta", "links"))
    assert all(k in response.json["data"] for k in ("type", "id", "attributes"))
    attributes = response.json["data"]["attributes"]
    assert (features := attributes.get("features"))
    assert (auth := features.get("auth_mechanisms"))
    assert auth["github"] is bool(
        os.environ.get("GITHUB_OAUTH_CLIENT_ID", None)
        and os.environ.get("GITHUB_OAUTH_CLIENT_SECRET", None)
    )
    assert auth["orcid"] is bool(
        os.environ.get("ORCID_OAUTH_CLIENT_ID", None)
        and os.environ.get("ORCID_OAUTH_CLIENT_SECRET", None)
    )
    assert auth["email"] is bool(os.environ.get("MAIL_PASSWORD", None))


@pytest.mark.parametrize("url_prefix", ["", "/v0", "/v0.1", "/v0.1.0"])
def test_healthcheck_is_alive_endpoint(client, url_prefix):
    response = client.get(f"{url_prefix}/healthcheck/is_alive")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["message"] == "Server is alive"


@pytest.mark.parametrize("url_prefix", ["", "/v0", "/v0.1", "/v0.1.0"])
def test_healthcheck_is_ready_endpoint(client, url_prefix):
    response = client.get(f"{url_prefix}/healthcheck/is_ready")
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["message"] == "Server and database are ready"


@pytest.mark.parametrize("url_prefix", ["", "/v0", "/v0.1", "/v0.1.0"])
def test_block_info_endpoint(client, url_prefix):
    response = client.get(f"{url_prefix}/info/blocks", follow_redirects=True)
    assert response.status_code == 200
    assert all(k in response.json for k in ("data", "meta"))
    for block in response.json["data"]:
        assert all(k in block for k in ("type", "id", "attributes"))
        assert all(
            k in block["attributes"] for k in ("name", "description", "accepted_file_extensions")
        )


def test_types_info_endpoint(client):
    response = client.get("/info/types", follow_redirects=True)
    assert response.status_code == 200
    assert all(k in response.json for k in ("data", "meta"))
    for _type in response.json["data"]:
        type_id = _type["id"]
        type_response = client.get(f"/info/types/{type_id}", follow_redirects=True)
        assert type_response.status_code == 200
        assert all(k in type_response.json for k in ("data", "meta"))
        type_obj = type_response.json["data"]
        assert all(k in type_obj for k in ("type", "id", "attributes"))
        assert type_obj["id"] == type_id
        assert type_obj["type"] == "item_type"
        assert type_obj["attributes"]["schema"]

    response = client.get("/info/types/random-type-that-doesnt-exist", follow_redirects=True)
    assert response.status_code == 404
