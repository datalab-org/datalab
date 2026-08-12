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


def test_location_endpoint(client, item_creator, user_id):
    item_creator(
        Cell(
            **{
                "item_id": "test_cell0",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 2.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 2.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 2000,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 100, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Place1>Place2>Place3",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_2",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Place1>Place2",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_3",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Place4>Place5>Place6",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_4",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Place1>Place7>Place8",
            }
        )
    )
    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(
        {
            "Place1>Place2>Place3",
            "Place1>Place2",
            "Place4>Place5>Place6",
            "Place1>Place7>Place8",
        }
    )

    # non-flat checks
    assert "nested_locations" in response.json
    assert response.json["nested_locations"]
    print(response.json["nested_locations"])
    assert "Place4" in response.json["nested_locations"]
    assert "Place5" in response.json["nested_locations"]["Place4"]
    assert "Place6" in response.json["nested_locations"]["Place4"]["Place5"]
    assert "Place1" in response.json["nested_locations"]
    assert "Place2" in response.json["nested_locations"]["Place1"]
    assert "Place7" in response.json["nested_locations"]["Place1"]
    assert "Place3" in response.json["nested_locations"]["Place1"]["Place2"]
    assert "Place8" in response.json["nested_locations"]["Place1"]["Place7"]


def test_location_endpoint_with_spaced_signs(client, item_creator, user_id):
    item_creator(
        Cell(
            **{
                "item_id": "test_cell0",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 2.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 2.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 2000,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 100, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Lab 1 > Shelf 2",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_2",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Lab 1 > Shelf 3",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_3",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Lab 2 > Shelf 1",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_4",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Lab 1 > Shelf 2 > Position A",
            }
        )
    )
    response = client.get("/locations")
    assert response.status_code == 200
    assert "flat_locations" in response.json

    assert set(response.json["flat_locations"]).issuperset(
        {
            "Lab 1 > Shelf 2",
            "Lab 1 > Shelf 3",
            "Lab 2 > Shelf 1",
            "Lab 1 > Shelf 2 > Position A",
        }
    )
    assert "nested_locations" in response.json
    assert "Lab 1" in response.json["nested_locations"]
    assert "Shelf 2" in response.json["nested_locations"]["Lab 1"]
    assert "Shelf 3" in response.json["nested_locations"]["Lab 1"]
    assert "Position A" in response.json["nested_locations"]["Lab 1"]["Shelf 2"]

    assert "Lab 2" in response.json["nested_locations"]
    assert "Shelf 1" in response.json["nested_locations"]["Lab 2"]


def test_location_endpoint_with_single_non_nested_location(client, item_creator, user_id):
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_4",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Lab 1",
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
    # test ensures that items don't get over (i.e. Position A should not get overwritten)
    item_creator(
        Cell(
            **{
                "item_id": "test_cell_4",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 5.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 1.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 500,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 10, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Cambridge > Lab 6 > Shelf 2 > Position A",
            }
        )
    )
    item_creator(
        Cell(
            **{
                "item_id": "test_cell0",
                "name": "test cell",
                "date": "1970-02-01",
                "negative_electrode": [
                    {
                        "item": {"item_id": "test", "type": "starting_materials"},
                        "quantity": 2.0,
                        "unit": "mg",
                    },
                    {
                        "item": {"item_id": "test_carbon", "chemform": "C", "type": "samples"},
                        "quantity": 2.0,
                        "unit": "mg",
                    },
                ],
                "positive_electrode": [
                    {
                        "item": {
                            "item_id": "test_cathode",
                            "chemform": "LiCoO2",
                            "type": "samples",
                        },
                        "quantity": 2000,
                        "unit": "kg",
                    }
                ],
                "electrolyte": [
                    {"item": {"name": "inlined reference"}, "quantity": 100, "unit": "ml"}
                ],
                "cell_format": "swagelok",
                "type": "cells",
                "creator_ids": [user_id],
                "Location": "Cambridge > Lab 6 > Shelf 1",
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
