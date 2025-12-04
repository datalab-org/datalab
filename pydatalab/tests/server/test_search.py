import pytest


@pytest.mark.parametrize(
    "user,query,expected_user_names",
    [
        ("admin", "query=User", ["Test User", "Another User"]),
        ("admin", "query=Admin", ["Test Admin"]),
        ("admin", "query='Test'", ["Test User", "Test Admin"]),
        ("admin", "query='ser'", []),
        ("admin", "query='Another'", ["Another User"]),
    ],
)
def test_user_regex_search(
    user, query, expected_user_names, real_mongo_client, client, admin_client
):
    """Test that user search supports the same heuristic regex as item search."""
    if real_mongo_client is None:
        pytest.skip("Skipping search tests, not connected to real MongoDB")

    if user == "admin":
        response = admin_client.get(f"/search-users/?{query}")
    else:
        response = client.get(f"/search-users/?{query}")

    assert response.status_code == 200, f"Failed with: {response.json}"
    assert response.json["status"] == "success"

    user_display_names = [
        u.get("display_name") for u in response.json["users"] if u.get("display_name")
    ]

    if expected_user_names:
        for expected_name in expected_user_names:
            assert any(expected_name in name for name in user_display_names), (
                f"Expected user {expected_name!r} not found in {user_display_names}"
            )


@pytest.mark.parametrize(
    "query,should_find",
    [
        ("query=test", True),
        ("query='test'", True),
        ("query='est'", False),
        ("query='collection'", True),
        ("query=%23est", True),
    ],
)
def test_collection_regex_search(query, should_find, real_mongo_client, client, default_collection):
    """Test that collection search supports the same heuristic regex as item search."""
    if real_mongo_client is None:
        pytest.skip("Skipping search tests, not connected to real MongoDB")

    test_collection = default_collection.dict()
    clean_query = query.replace("=", "_").replace("%23", "hash_").replace("'", "")
    test_collection["collection_id"] = f"test_coll_{clean_query}"
    test_collection["title"] = "test collection"

    response = client.put("/collections", json={"data": test_collection})
    assert response.status_code == 201, f"Failed to create collection: {response.json}"

    response = client.get(f"/search-collections/?{query}")

    assert response.status_code == 200, f"Search failed: {response.json}"
    assert response.json["status"] == "success"

    collection_ids = [c["collection_id"] for c in response.json["data"]]

    if should_find:
        assert test_collection["collection_id"] in collection_ids, (
            f"Expected collection not found for {query=}. Found: {collection_ids}"
        )

    client.delete(f"/collections/{test_collection['collection_id']}")
