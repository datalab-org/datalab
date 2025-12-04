import pytest


@pytest.mark.parametrize("url_prefix", ["", "/v0", "/v0.1", "/v0.1.0"])
def test_info_endpoint(client, url_prefix, app):
    response = client.get(f"{url_prefix}/info")
    assert response.status_code == 200
    assert all(k in response.json for k in ("data", "meta", "links"))
    assert all(k in response.json["data"] for k in ("type", "id", "attributes"))
    attributes = response.json["data"]["attributes"]
    assert (features := attributes.get("features"))
    assert (auth := features.get("auth_mechanisms"))
    assert auth["github"] is bool(
        app.config.get("GITHUB_OAUTH_CLIENT_ID", None)
        and app.config.get("GITHUB_OAUTH_CLIENT_SECRET", None)
    )
    assert auth["orcid"] is bool(
        app.config.get("ORCID_OAUTH_CLIENT_ID", None)
        and app.config.get("ORCID_OAUTH_CLIENT_SECRET", None)
    )
    assert auth["email"] is bool(app.config.get("MAIL_PASSWORD", None))


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
            k in block["attributes"]
            for k in ("name", "description", "accepted_file_extensions", "version")
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


def test_info_endpoint_includes_max_upload_bytes(client, app):
    """Test that the /info endpoint includes the max_upload_bytes configuration."""
    response = client.get("/info")
    assert response.status_code == 200
    assert "data" in response.json
    assert "attributes" in response.json["data"]
    attributes = response.json["data"]["attributes"]
    assert "max_upload_bytes" in attributes
    assert isinstance(attributes["max_upload_bytes"], int)
    assert attributes["max_upload_bytes"] > 0
    assert attributes["max_upload_bytes"] == 10 * 1000 * 1000
