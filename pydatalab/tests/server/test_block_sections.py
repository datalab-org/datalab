import pytest

from pydatalab.models.blocks import HasBlocks, Section


def _section(section_id="section_sem", title="SEM images", description=None):
    return {
        "type": "section",
        "section_id": section_id,
        "title": title,
        "description": description,
    }


@pytest.fixture()
def sample_with_blocks(admin_client, default_sample_dict, random_string):
    """Create a fresh sample with two comment blocks attached, returning
    `(sample_id, [block_id, ...])`."""
    sample_id = f"test_sections_{random_string[:10]}"
    sample_data = default_sample_dict.copy()
    sample_data["item_id"] = sample_id

    response = admin_client.post("/new-sample/", json=sample_data)
    assert response.status_code == 201, response.json

    block_ids = []
    for _ in range(2):
        response = admin_client.post(
            "/add-data-block/",
            json={"block_type": "comment", "item_id": sample_id, "index": None},
        )
        assert response.status_code == 200, response.json
        block_ids.append(response.json["new_block_obj"]["block_id"])

    yield sample_id, block_ids

    admin_client.post("/delete-sample/", json={"item_id": sample_id})


def _get_item_data(client, sample_id):
    response = client.get(f"/get-item-data/{sample_id}")
    assert response.status_code == 200, response.json
    return response.json["item_data"]


def _save_display_order(client, sample_id, display_order):
    item_data = _get_item_data(client, sample_id)
    item_data["display_order"] = display_order
    return client.post("/save-item/", json={"item_id": sample_id, "data": item_data})


def test_display_order_accepts_sections():
    model = HasBlocks(display_order=["block_a", _section(), "block_b"])
    assert model.display_order[0] == "block_a"
    assert isinstance(model.display_order[1], Section)
    assert model.display_order[1].title == "SEM images"
    assert model.display_order[2] == "block_b"


def test_section_requires_an_id_and_a_title():
    with pytest.raises(ValueError):
        HasBlocks(display_order=[{"type": "section", "title": "No ID"}])
    with pytest.raises(ValueError):
        HasBlocks(display_order=[{"type": "section", "section_id": "section_no_title"}])


def test_sections_round_trip_through_save(sample_with_blocks, admin_client):
    sample_id, (first_block, second_block) = sample_with_blocks
    display_order = [
        first_block,
        _section(description="<p>Ten SEM images</p>"),
        second_block,
    ]

    response = _save_display_order(admin_client, sample_id, display_order)
    assert response.status_code == 200, response.json

    assert _get_item_data(admin_client, sample_id)["display_order"] == display_order


def test_invalid_section_is_rejected_on_save(sample_with_blocks, admin_client):
    sample_id, (first_block, second_block) = sample_with_blocks
    stored_order = _get_item_data(admin_client, sample_id)["display_order"]

    response = _save_display_order(
        admin_client,
        sample_id,
        [first_block, {"type": "section", "section_id": "section_no_title"}, second_block],
    )
    assert response.status_code == 400, response.json

    assert _get_item_data(admin_client, sample_id)["display_order"] == stored_order


def test_blocks_can_be_added_and_deleted_alongside_sections(sample_with_blocks, admin_client):
    sample_id, (first_block, second_block) = sample_with_blocks
    section = _section()
    response = _save_display_order(admin_client, sample_id, [first_block, section, second_block])
    assert response.status_code == 200, response.json

    response = admin_client.post(
        "/add-data-block/",
        json={"block_type": "comment", "item_id": sample_id, "index": None},
    )
    assert response.status_code == 200, response.json
    new_block = response.json["new_block_obj"]["block_id"]
    assert response.json["new_display_order"] == [first_block, section, second_block, new_block]

    response = admin_client.post(
        "/delete-block/", json={"item_id": sample_id, "block_id": second_block}
    )
    assert response.status_code == 200, response.json

    assert _get_item_data(admin_client, sample_id)["display_order"] == [
        first_block,
        section,
        new_block,
    ]
