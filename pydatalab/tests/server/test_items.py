from pydatalab.models import Cell


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
    from pydatalab.mongo import get_items_fts_fields

    fields = ("item_id", "name", "description", "refcode", "synthesis_description", "supplier")
    assert all(field in get_items_fts_fields() for field in fields)


def test_location_endpoint_server_defaults(client, item_creator, user_id):
    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(
        {"Cambridge > Lab 1 > Location A", "Cambridge > Lab 2"}
    )

    # non-flat checks
    assert "nested_locations" in response.json
    assert response.json["nested_locations"] is not None
    assert "Cambridge" in response.json["nested_locations"]
    assert "Lab 1" in response.json["nested_locations"]["Cambridge"]
    assert "Lab 2" in response.json["nested_locations"]["Cambridge"]
    assert "Location A" in response.json["nested_locations"]["Cambridge"]["Lab 1"]


def test_location_endpoint(client, item_creator, user_id):
    locations = [
        "Place1>Place2>Place3",
        "Place1>Place2",
        "Place4>Place5>Place6",
        "Place1>Place7>Place8",
    ]
    for ind, loc in enumerate(locations):
        cell = Cell(**{"item_id": f"test_cell_{ind + 10}", "location": loc})
        item_creator(cell)

    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json
    assert set(response.json["flat_locations"]).issuperset(set(locations))

    # non-flat checks
    assert "nested_locations" in response.json
    assert response.json["nested_locations"] is not None
    assert "Place4" in response.json["nested_locations"]
    assert "Place5" in response.json["nested_locations"]["Place4"]
    assert "Place6" in response.json["nested_locations"]["Place4"]["Place5"]
    assert "Place1" in response.json["nested_locations"]
    assert "Place2" in response.json["nested_locations"]["Place1"]
    assert "Place7" in response.json["nested_locations"]["Place1"]
    assert "Place3" in response.json["nested_locations"]["Place1"]["Place2"]
    assert "Place8" in response.json["nested_locations"]["Place1"]["Place7"]


def test_location_endpoint_with_spaced_signs(client, item_creator, user_id):
    locations = [
        "Lab 1 > Shelf 2",
        "Lab 1 > Shelf 3",
        "Lab 2 > Shelf 1",
        "Lab 1 > Shelf 2 > Position A",
    ]
    for ind, loc in enumerate(locations):
        cell = Cell(**{"item_id": f"test_cell_{ind + 20}", "location": loc})
        item_creator(cell)

    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(set(locations))
    assert "nested_locations" in response.json
    assert "Lab 1" in response.json["nested_locations"]
    assert "Shelf 2" in response.json["nested_locations"]["Lab 1"]
    assert "Shelf 3" in response.json["nested_locations"]["Lab 1"]
    assert "Position A" in response.json["nested_locations"]["Lab 1"]["Shelf 2"]

    assert "Lab 2" in response.json["nested_locations"]
    assert "Shelf 1" in response.json["nested_locations"]["Lab 2"]


def test_location_endpoint_with_bad_segments(client, item_creator):
    """Tests that malformed locations (e.g., double >) do not break endpoint."""

    locations = [
        "Lab 1 >> Shelf 2",
        "Building A > Lab 1 > Shelf 3",
        "Shelf 3",
        ">>>>>>>>>>",
        "<<<<",
    ]

    for ind, loc in enumerate(locations):
        item_creator(Cell(**{"item_id": f"test_cell_{ind + 99}", "location": loc}))

    # expected_nest = {"Lab 1": ["Shelf 2"], "Building A": {"Lab 1": ["Shelf 3"], "Shelf 3": {}}}

    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(locations)
    assert "nested_locations" in response.json
    assert all(k in response.json["nested_locations"] for k in ["Lab 1", "Building A", "Shelf 3"])
    assert response.json["nested_locations"]["Building A"]["Lab 1"] == {"Shelf 3": {}}
    assert response.json["nested_locations"]["Shelf 3"] == {}
    assert response.json["nested_locations"]["Lab 1"] == {"Shelf 2": {}}


def test_location_endpoint_with_duplicated_segments(client, item_creator):
    """Tests that duplicated segments appearing at different levels
    are treated as separate things.

    """

    locations = ["Lab 1 > Shelf 2", "Building A > Lab 1 > Shelf 3", "Shelf 3"]

    for ind, loc in enumerate(locations):
        item_creator(Cell(**{"item_id": f"test_cell_{ind + 99}", "location": loc}))

    # expected_nest = {"Lab 1": ["Shelf 2"], "Building A": {"Lab 1": ["Shelf 3"], "Shelf 3": {}}}

    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(locations)
    assert "nested_locations" in response.json
    assert all(k in response.json["nested_locations"] for k in ["Lab 1", "Building A", "Shelf 3"])
    assert response.json["nested_locations"]["Building A"]["Lab 1"] == {"Shelf 3": {}}
    assert response.json["nested_locations"]["Shelf 3"] == {}
    assert response.json["nested_locations"]["Lab 1"] == {"Shelf 2": {}}


def test_location_endpoint_with_single_non_nested_location(client, item_creator, user_id):
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_4",
                "location": "Lab 1",
            }
        )
    )
    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset({"Lab 1"})
    assert "nested_locations" in response.json
    assert "Lab 1" in response.json["nested_locations"]


def test_regression_test_against_overwriting_problem(client, item_creator, user_id):
    # test ensures that items don't get overwritten (i.e. Position A should not get overwritten)
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_4",
                "location": "Cambridge > Lab 6 > Shelf 2 > Position A",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell0",
                "location": "Cambridge > Lab 6 > Shelf 1",
            }
        )
    )

    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(
        {
            "Cambridge > Lab 6 > Shelf 1",
            "Cambridge > Lab 6 > Shelf 2 > Position A",
        }
    )
    assert "nested_locations" in response.json
    assert "Cambridge" in response.json["nested_locations"]
    assert "Lab 6" in response.json["nested_locations"]["Cambridge"]
    assert "Shelf 1" in response.json["nested_locations"]["Cambridge"]["Lab 6"]
    assert "Shelf 2" in response.json["nested_locations"]["Cambridge"]["Lab 6"]
    assert "Position A" in response.json["nested_locations"]["Cambridge"]["Lab 6"]["Shelf 2"]
