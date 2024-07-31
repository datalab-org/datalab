def test_single_item_endpoints(client, inserted_default_items):
    for item in inserted_default_items:
        response = client.get(f"/items/{item.refcode}")
        assert response.status_code == 200, response.json
        assert response.json["status"] == "success"

        test_ref = item.refcode.split(":")[1]
        response = client.get(f"/items/{test_ref}")
        assert response.status_code == 200, response.json
        assert response.json["status"] == "success"

        response = client.get(f"/get-item-data/{item.item_id}")
        assert response.status_code == 200, response.json
        assert response.json["status"] == "success"
