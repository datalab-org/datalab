import datetime
import json

import pydantic
import pytest
from bson.json_util import ObjectId

from pydatalab.models import ITEM_MODELS, Sample
from pydatalab.models.files import File
from pydatalab.models.items import Item
from pydatalab.models.people import DisplayName, EmailStr
from pydatalab.models.relationships import (
    KnownType,
    RelationshipType,
    TypedRelationship,
)
from pydatalab.models.utils import HumanReadableIdentifier, Refcode


def test_sample_with_inlined_reference():
    from pydatalab.models.samples import Sample

    a = Sample(item_id="test_anode", chemform="C")

    b = Sample(
        item_id="abcd-1-2-3",
        synthesis_constituents=[
            {"item": {"item_id": a.item_id, "type": "samples"}, "quantity": None}
        ],
    )

    assert b
    assert len(b.relationships) == 1

    c = Sample(
        item_id="c-123",
        synthesis_constituents=[
            {"item": {"item_id": a.item_id, "type": "samples"}, "quantity": None},
            {"item": {"name": "inline"}, "quantity": None},
        ],
    )

    assert c
    assert len(c.relationships) == 1

    d = Sample(
        item_id="d-123",
        synthesis_constituents=[
            {"item": {"name": a.item_id}, "quantity": None},
            {"item": {"name": "inline"}, "quantity": None},
        ],
    )
    assert d
    assert len(d.relationships) == 0


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


def test_file():
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    file_dict1 = {
        "_id": "6437c96341ffc8169a957e2d",
        "size": 10003,
        "last_modified_remote": "2019-05-18T15:17:08",
        "item_ids": ["test1", "test2"],
        "blocks": ["123456"],
        "name": "test.jpg",
        "extension": ".jpg",
        "original_name": "test .jpg",
        "location": "path/test.jpg",
        "url_path": "/app/files/dsefse/test.jpg",
        "source": "remote",
        "time_added": current_datetime,
        "metadata": {"something": "data"},
        "representation": [1, 2, 3],
        "source_server_name": "Bob",
        "source_path": "test_experiment/pictures/test.jpg",
        "is_live": True,
    }

    # maximal file (everything defined)
    File1 = File(**file_dict1)
    assert File1.type == "files"
    assert File1.time_added == current_datetime

    file_dict2 = {
        "item_ids": [],
        "blocks": [],
        "name": "a.b",
        "extension": ".b",
        "time_added": "2019-05-18T15:18:10",
        "is_live": False,
    }

    # minimal file
    File2 = File(**file_dict2)
    assert File2.type == "files"
    assert File2.time_added == datetime.datetime.fromisoformat("2019-05-18T15:18:10").replace(
        tzinfo=datetime.timezone.utc
    )

    # make sure you can make a sample with the files internal
    sample = Sample(
        creator_ids=[ObjectId("0123456789ab0123456789ab"), ObjectId("1023456789ab0123456789ab")],
        creators=None,
        date="2020-01-01 00:00",
        last_modified=datetime.datetime(2020, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
        item_id="1234",
        files=[file_dict1, file_dict2],
    )

    assert sample.files[0].type == "files"
    assert sample.files[1].type == "files"


def test_custom_and_inherited_items():
    class TestItem(Item):
        type: str = "items_custom"

    item = TestItem(
        type="items_custom",
        last_modified=None,
        creator_ids=[ObjectId("0123456789ab0123456789ab"), ObjectId("1023456789ab0123456789ab")],
        creators=None,
        date="2020-01-01 00:00",
        item_id="1234",
    )

    item_dict = item.dict()
    assert item_dict["type"] == "items_custom"
    assert item_dict["creator_ids"][0] == ObjectId("0123456789ab0123456789ab")
    assert item_dict["creator_ids"][1] == ObjectId("1023456789ab0123456789ab")
    assert item_dict["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00").replace(
        tzinfo=datetime.timezone.utc
    )

    item_json = json.loads(item.json())
    assert item_json["type"] == "items_custom"
    assert item_json["creator_ids"][0] == str(ObjectId("0123456789ab0123456789ab"))
    assert item_json["creator_ids"][1] == str(ObjectId("1023456789ab0123456789ab"))
    assert (
        item_json["date"]
        == datetime.datetime.fromisoformat("2020-01-01 00:00")
        .replace(tzinfo=datetime.timezone.utc)
        .isoformat()
    )

    sample = Sample(
        creator_ids=[ObjectId("0123456789ab0123456789ab"), ObjectId("1023456789ab0123456789ab")],
        creators=None,
        date="2020-01-01 00:00",
        last_modified=datetime.datetime(2020, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
        item_id="1234",
    )

    sample_dict = sample.dict()
    assert sample_dict["type"] == "samples"
    assert sample_dict["creator_ids"][0] == ObjectId("0123456789ab0123456789ab")
    assert sample_dict["creator_ids"][1] == ObjectId("1023456789ab0123456789ab")
    assert sample_dict["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00").replace(
        tzinfo=datetime.timezone.utc
    )
    assert sample_dict["last_modified"] == datetime.datetime.fromisoformat(
        "2020-01-01 00:00"
    ).replace(tzinfo=datetime.timezone.utc)

    sample_json = json.loads(sample.json())
    assert sample_json["type"] == "samples"
    assert sample_json["creator_ids"][0] == str(ObjectId("0123456789ab0123456789ab"))
    assert sample_json["creator_ids"][1] == str(ObjectId("1023456789ab0123456789ab"))
    assert (
        sample_json["date"]
        == datetime.datetime.fromisoformat("2020-01-01 00:00")
        .replace(tzinfo=datetime.timezone.utc)
        .isoformat()
    )
    assert (
        sample_json["last_modified"]
        == datetime.datetime.fromisoformat("2020-01-01 00:00")
        .replace(tzinfo=datetime.timezone.utc)
        .isoformat()
    )


@pytest.mark.parametrize(
    "id",
    [
        "1234",
        "jmas-1-24-2020-5",
        "MP2018_TEST_COMMERCIAL",
        "MP2018_TEST_COMMERCIAL_4.5V_hold",
        "AAAAAA",
        111111111,
    ],
)
def test_good_ids(id):
    """Test good human-readable IDs for validity."""

    assert HumanReadableIdentifier(id)


@pytest.mark.parametrize(
    "id",
    [
        "MP2018(W/O)",
        "mp 1 2 3 4 5 6",
        "lithium & sodium",
        "me388-123456789-123456789-really-long-descriptive-identifier-that-should-be-the-name-but-is-otherwise-valid",
        1111111111111111111111111111111111111111111111111,
        "_AAAA",
        "AAA_",
        "Asadasd.",
        "__",
        "_",
    ],
)
def test_bad_ids(id):
    """Test bad human-readable IDs for invalidity."""

    with pytest.raises(pydantic.ValidationError):
        HumanReadableIdentifier(id)


def test_cell_with_inlined_reference():
    from pydatalab.models.cells import Cell
    from pydatalab.models.samples import Sample

    anode = Sample(item_id="test_anode", chemform="C")

    cell = Cell(
        item_id="abcd-1-2-3",
        positive_electrode=[{"item": anode, "quantity": 2}],
        negative_electrode=[
            {"item": {"name": "My secret cathode", "chemform": "NaCoO2"}, "quantity": 3}
        ],
        characteristic_mass=1.2,
        active_ion="Na+",
        cell_format="swagelok",
    )

    assert cell
    assert len(cell.relationships) == 1

    cell = Cell(**json.loads(cell.json()))
    assert cell
    assert len(cell.relationships) == 1

    # test from raw json
    cell_json = {
        "item_id": "abcd-1-2-3",
        "positive_electrode": [
            {"item": {"type": "samples", "item_id": "test_anode", "chemform": "C"}, "quantity": 2}
        ],
        "negative_electrode": [
            {"item": {"name": "My secret cathode", "chemform": "NaCoO2"}, "quantity": 3}
        ],
        "characteristic_mass": 1.2,
        "active_ion": "Na+",
        "cell_format": "swagelok",
    }

    cell = Cell(**cell_json)
    assert cell
    assert len(cell.relationships) == 1

    cell_json_2 = {
        "item_id": "abcd-1-2-3",
        "positive_electrode": [
            {"item": {"item_id": "", "name": "inline", "chemform": "C"}, "quantity": 2}
        ],
        "negative_electrode": [
            {"item": {"name": "My secret cathode", "chemform": "NaCoO2"}, "quantity": 3}
        ],
        "characteristic_mass": 1.2,
        "active_ion": "Na+",
        "cell_format": "swagelok",
    }

    cell = Cell(**cell_json_2)
    assert cell
    assert len(cell.relationships) == 0

    cell_json_3 = {
        "item_id": "abcd-1-2-3",
        "positive_electrode": [
            {"item": {"type": "samples", "item_id": "real_item"}, "quantity": 2}
        ],
        "negative_electrode": [
            {"item": {"name": "My secret cathode", "chemform": "NaCoO2"}, "quantity": 3}
        ],
        "characteristic_mass": 1.2,
        "active_ion": "Na+",
        "cell_format": "swagelok",
    }

    cell = Cell(**cell_json_3)
    assert cell
    assert len(cell.relationships) == 1


def test_molar_mass():
    import math

    from periodictable import formula

    test_formulae = [
        ("H2O", 18.01528),
        ("LiNi0.8Co0.1Mn0.1O2", 97.28),
        ("Li10Ni8CoMnO20", 972.8),
        ("Li10.1Ni8CoMnO20", 973.5),
    ]

    for form, mass in test_formulae:
        assert math.isclose(formula(form).mass, mass, rel_tol=1e-3)


@pytest.mark.parametrize(
    "refcode",
    [
        "grey:ABCDEF",
        "grey:ABC_DEF",
        "grey:ABC_DE_F",
        "grey:a2f2b2asdfadsf",
        "grey:a2-f2b-2a-sd-fadsf",
        "grey:a2_f2b_2a_sd_fadsf",
        "grey:AaAaAa",
        "grey:Aa.Aa.Aa",
        "grey:A",
        "grey:AA",
        "whatever:123456",
    ],
)
def test_good_refcodes(refcode):
    """Test good refcodes for validity."""

    assert Refcode(refcode)


@pytest.mark.parametrize(
    "refcode",
    [
        "AAAAAA",
        "grey:1111111111111111111111111111111111111111111111111111111111111111111",
        "grey:hello_refcode_",
        "grey:hello_refcode-",
        "grey:_hello_refcode",
        "prefixwaytoolongasdfasdf:ABACUF",
        "BadPrefix:ABACUF",
        "Bad_Prefix:ABACUF",
        "a:ABACUF",
        "grey:_",
    ],
)
def test_bad_refcodes(refcode):
    """Test bad refcodes for invalidity."""

    with pytest.raises(pydantic.ValidationError):
        Refcode(refcode)


@pytest.mark.parametrize(
    "display_name",
    [
        "Test",
        "Test Test",
        "Test test test",
        "约翰·史密斯",
    ],
)
def test_good_display_name(display_name):
    """Test good display name for validity."""

    assert DisplayName(display_name)


@pytest.mark.parametrize(
    "display_name",
    [
        "",
        " ",
        "Test" * 100,
    ],
)
def test_bad_display_name(display_name):
    """Test bad display_name for invalidity."""

    with pytest.raises(ValueError):
        DisplayName(display_name)


@pytest.mark.parametrize(
    "contact_email",
    [
        "test@example.com",
    ],
)
def test_good_email(contact_email):
    assert EmailStr(contact_email)


@pytest.mark.parametrize(
    "contact_email",
    [
        "test@example.com2",
        "   ",
        "test@",
        1000 * "test" + "@example.com",
    ],
)
def test_bad_email(contact_email):
    with pytest.raises(ValueError):
        assert EmailStr(contact_email)
