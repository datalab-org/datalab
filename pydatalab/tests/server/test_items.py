def test_single_item_endpoints(client, inserted_default_items):
    for item in inserted_default_items:
        response = client.get(f"/items/{item.refcode}")
        assert response.status_code == 200, response.json
        assert response.json["item_id"] == item.item_id
        assert response.json["item_data"]["item_id"] == item.item_id
        assert response.json["status"] == "success"

        test_ref = item.refcode.split(":")[1]
        response = client.get(f"/items/{test_ref}")
        assert response.status_code == 200, response.json
        assert response.json["item_id"] == item.item_id
        assert response.json["item_data"]["item_id"] == item.item_id
        assert response.json["status"] == "success"

        response = client.get(f"/get-item-data/{item.item_id}")
        assert response.status_code == 200, response.json
        assert response.json["status"] == "success"
        assert response.json["item_id"] == item.item_id
        assert response.json["item_data"]["item_id"] == item.item_id


def test_fts_fields():
    """Test non-exhaustively that certain fields make it into the fts index."""
    from pydatalab.mongo import ITEMS_FTS_FIELDS

    fields = ("item_id", "name", "description", "refcode", "synthesis_description", "supplier")
    assert all(field in ITEMS_FTS_FIELDS for field in fields)
