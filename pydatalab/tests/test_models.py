import datetime
import json

import pydantic
import pytest
from bson.json_util import ObjectId

from pydatalab.models import ITEM_MODELS, Sample
from pydatalab.models.items import Item
from pydatalab.models.relationships import (
    KnownType,
    RelationshipType,
    TypedRelationship,
)
from pydatalab.models.utils import HumanReadableIdentifier


@pytest.mark.parametrize("model", ITEM_MODELS.values())
def test_generate_schemas(model):
    """Test that all item model schemas can be generated."""
    assert model.schema()


def test_relationship_with_custom_type():
    """Test that a relationship with a custom type can be created."""
    relationship = TypedRelationship(
        relation=RelationshipType.OTHER,
        type=KnownType.SAMPLES,
        item_id="1234",
        description="This is a relationship",
    )
    assert relationship.relation == RelationshipType.OTHER
    assert relationship.type == KnownType.SAMPLES
    assert relationship.item_id == "1234"
    assert relationship.description == "This is a relationship"

    with pytest.raises(pydantic.ValidationError):
        relationship = TypedRelationship(
            relation=RelationshipType.OTHER,
            type=KnownType.SAMPLES,
            item_id="1234",
            description=None,
        )


def test_custom_and_inherited_items():
    class TestItem(Item):
        type: str = "items_custom"

    item = TestItem(
        type="items_custom",
        last_modified=None,
        creator_ids=[ObjectId("0123456789ab0123456789ab"), ObjectId("1023456789ab0123456789ab")],
        creators=None,
        files=["file1", "file2"],
        date="2020-01-01 00:00",
        item_id="1234",
    )

    item_dict = item.dict()
    assert item_dict["type"] == "items_custom"
    assert item_dict["creator_ids"][0] == ObjectId("0123456789ab0123456789ab")
    assert item_dict["creator_ids"][1] == ObjectId("1023456789ab0123456789ab")
    assert item_dict["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00")

    item_json = json.loads(item.json())
    assert item_json["type"] == "items_custom"
    assert item_json["creator_ids"][0] == str(ObjectId("0123456789ab0123456789ab"))
    assert item_json["creator_ids"][1] == str(ObjectId("1023456789ab0123456789ab"))
    assert item_json["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00").isoformat()

    sample = Sample(
        creator_ids=[ObjectId("0123456789ab0123456789ab"), ObjectId("1023456789ab0123456789ab")],
        creators=None,
        files=["file1", "file2"],
        date="2020-01-01 00:00",
        last_modified=datetime.datetime(2020, 1, 1, 0, 0),
        item_id="1234",
    )

    sample_dict = sample.dict()
    assert sample_dict["type"] == "samples"
    assert sample_dict["creator_ids"][0] == ObjectId("0123456789ab0123456789ab")
    assert sample_dict["creator_ids"][1] == ObjectId("1023456789ab0123456789ab")
    assert sample_dict["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00")
    assert sample_dict["last_modified"] == datetime.datetime.fromisoformat("2020-01-01 00:00")

    sample_json = json.loads(sample.json())
    assert sample_json["type"] == "samples"
    assert sample_json["creator_ids"][0] == str(ObjectId("0123456789ab0123456789ab"))
    assert sample_json["creator_ids"][1] == str(ObjectId("1023456789ab0123456789ab"))
    assert sample_json["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00").isoformat()
    assert (
        sample_json["last_modified"]
        == datetime.datetime.fromisoformat("2020-01-01 00:00").isoformat()
    )


@pytest.mark.parametrize(
    "id",
    [
        "1234",
        "jmas-1-24-2020-5",
        "MP2018_TEST_COMMERCIAL",
        "AAAAAA",
        111111111,
    ],
)
def test_good_ids(id):
    """Test good human-readable IDs for validity.

    Has to go via a model to test the validator (see docstring for `HumanReadableIdentifier`).

    """

    class DummyModel(pydantic.BaseModel):
        id: HumanReadableIdentifier

    assert DummyModel(id=id)


@pytest.mark.parametrize(
    "id",
    [
        "MP2018(W/O)",
        "mp 1 2 3",
        "lithium & sodium",
        "me388-123456789-123456789-really-long-descriptive-identifier-that-should-be-the-name-but-is-otherwise-valid",
        1111111111111111111111111111111111111111111111111,
    ],
)
def test_bad_ids(id):
    """Test bad human-readable IDs for invalidity.

    Has to go via a model to test the validator (see docstring for `HumanReadableIdentifier`).

    """

    class DummyModel(pydantic.BaseModel):
        id: HumanReadableIdentifier

    with pytest.raises(pydantic.ValidationError):
        DummyModel(id=id)
