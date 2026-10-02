# This file was edited with the assistance of an AI model and requires human review from the contributor.
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
    RelationshipType,
    TypedRelationship,
)
from pydatalab.models.utils import HumanReadableIdentifier, Refcode


def test_sample_with_inlined_reference():
    from pydatalab.models.relationships import RelationshipType
    from pydatalab.models.samples import Sample

    a = Sample(item_id="test_anode", refcode="test:ANODE", chemform="C")

    b = Sample(
        item_id="abcd-1-2-3",
        synthesis_constituents=[
            {"item": {"item_id": a.item_id, "type": "samples"}, "quantity": None}
        ],
    )

    assert b
    assert len(b.relationships) == 1
    # A constituent referenced by item_id alone produces a relationship keyed on item_id
    assert b.relationships[0].item_id == a.item_id
    assert b.relationships[0].refcode is None

    # A constituent carrying both identifiers should propagate both onto the
    # relationship, and re-validation must not duplicate it.
    b_both = Sample(
        item_id="abcd-1-2-3",
        synthesis_constituents=[
            {
                "item": {"item_id": a.item_id, "refcode": a.refcode, "type": "samples"},
                "quantity": None,
            }
        ],
    )
    parents = [r for r in b_both.relationships if r.relation == RelationshipType.PARENT]
    assert len(parents) == 1
    assert parents[0].item_id == a.item_id
    assert parents[0].refcode == a.refcode

    b_both = Sample(**json.loads(b_both.model_dump_json()))
    parents = [r for r in b_both.relationships if r.relation == RelationshipType.PARENT]
    assert len(parents) == 1

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
    assert model.model_json_schema()


def test_attribute_docstrings_in_schema():
    """Field docstrings should be pulled into the JSON schema as descriptions.

    Relies on ``use_attribute_docstrings`` being set on the shared ``BaseModel``
    in ``pydatalab.models.utils``; covers fields defined across several different
    trait mixins to confirm the config propagates through inheritance.
    """
    properties = Sample.model_json_schema(by_alias=False)["properties"]

    expected = {
        "creators": "Inlined info for the people associated with this item.",  # HasOwner
        "blocks_obj": "A mapping from block ID to block data.",  # HasBlocks
        "revision": "The revision number of the entry.",  # HasRevisionControl
        "collections": "Inlined info for the collections associated with this item.",  # IsCollectable
        "name": "An optional human-readable/usable name for the entry.",  # Item
    }

    for field, description in expected.items():
        assert properties[field]["description"] == description


def test_relationship_with_custom_type():
    """Test that a relationship with a custom type can be created."""
    relationship = TypedRelationship(
        relation=RelationshipType.OTHER,
        type="samples",
        item_id="1234",
        description="This is a relationship",
    )
    assert relationship.relation == RelationshipType.OTHER
    assert relationship.type == "samples"
    assert relationship.item_id == "1234"
    assert relationship.description == "This is a relationship"

    with pytest.raises(pydantic.ValidationError):
        relationship = TypedRelationship(
            relation=RelationshipType.OTHER,
            type="samples",
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


def test_tag_model():
    from pydatalab.models.tags import Tag, TagAccessScope

    tag = Tag(name="test_tag", description="This is an example", color="#f1c40f", scope="global")
    assert tag.type == "tags"
    assert tag.name == "test_tag"
    assert tag.description == "This is an example"
    assert tag.color == "#f1c40f"
    assert tag.scope == TagAccessScope.GLOBAL
    assert tag.owner is None

    # Scope is modelled explicitly via `scope`/`owner` (not the `HasOwner` mixin).
    assert not hasattr(tag, "creator_ids")
    assert not hasattr(tag, "group_ids")

    oid = ObjectId("0123456789ab0123456789ab")
    doc = {"_id": oid, "type": "tags", "name": "glovebox", "scope": "global"}
    stored_tag = Tag(**doc)
    assert stored_tag.immutable_id == oid
    assert stored_tag.description is None
    assert stored_tag.color is None
    assert stored_tag.model_dump()["immutable_id"] == oid
    assert stored_tag.scope == TagAccessScope.GLOBAL

    # Both `name` and `scope` are required.
    with pytest.raises(pydantic.ValidationError):
        Tag(scope="global", description="missing a name")
    with pytest.raises(pydantic.ValidationError):
        Tag(name="missing-a-scope")


def test_tag_scope_owner_consistency():
    """A user-scoped tag must have an owner; a global tag must not."""
    from pydatalab.models.tags import Tag, TagAccessScope

    owner = ObjectId()

    # A valid user-defined tag.
    user_defined = Tag(name="mine", scope="user", owner=owner)
    assert user_defined.scope == TagAccessScope.USER
    assert user_defined.owner == owner
    # `owner` is preserved as an ObjectId in the stored (python-mode) dump.
    assert isinstance(user_defined.model_dump(exclude_none=True)["owner"], ObjectId)
    # ... and stringified in the JSON dump sent to clients.
    assert json.loads(user_defined.model_dump_json())["owner"] == str(owner)

    # A valid global tag has no owner.
    glob = Tag(name="shared", scope="global")
    assert glob.owner is None

    # A user-scoped tag without an owner is rejected.
    with pytest.raises(pydantic.ValidationError):
        Tag(name="bad", scope="user")

    # A global tag with an owner is rejected.
    with pytest.raises(pydantic.ValidationError):
        Tag(name="bad", scope="global", owner=owner)


def test_item_tags_coercion():
    """The `HasTags` mixin coerces references and de-duplicates tags on items."""
    from pydatalab.models.samples import Sample
    from pydatalab.models.utils import EntryReference

    oid = ObjectId("0123456789ab0123456789ab")

    sample = Sample(
        item_id="tagged",
        tags=[
            {"type": "tags", "immutable_id": str(oid), "name": "Curated"},
            {"type": "tags", "immutable_id": str(oid)},  # same reference by id -> dropped
        ],
    )

    assert len(sample.tags) == 1
    ref = sample.tags[0]
    assert isinstance(ref, EntryReference)
    assert ref.type == "tags"
    assert ref.immutable_id == oid
    assert ref.name == "Curated"

    # Default is an empty list, so existing tag-less documents stay valid.
    assert Sample(item_id="untagged").tags == []

    # A reference to a (possibly deleted) tag still validates.
    dangling = Sample(item_id="dangling", tags=[{"type": "tags", "immutable_id": str(ObjectId())}])
    assert len(dangling.tags) == 1

    # Bare string tags are not allowed: only references to tags entries.
    with pytest.raises(pydantic.ValidationError):
        Sample(item_id="string-tag", tags=["custom"])

    # Re-validating a dumped item round-trips the reference tags list.
    roundtrip = Sample(**json.loads(sample.model_dump_json()))
    assert [type(t).__name__ for t in roundtrip.tags] == ["EntryReference"]


def test_custom_and_inherited_items():
    class TestItem(Item):
        type: str = "items_custom"
        new_field: str

    TestItem.model_rebuild()

    item = TestItem(
        type="items_custom",
        last_modified=None,
        creator_ids=[ObjectId("0123456789ab0123456789ab"), ObjectId("1023456789ab0123456789ab")],
        creators=None,
        date="2020-01-01 00:00",
        item_id="1234",
        new_field="This is a new field",
    )

    item_dict = item.model_dump()
    assert item_dict["type"] == "items_custom"
    assert item_dict["creator_ids"][0] == ObjectId("0123456789ab0123456789ab")
    assert item_dict["creator_ids"][1] == ObjectId("1023456789ab0123456789ab")
    assert item_dict["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00").replace(
        tzinfo=datetime.timezone.utc
    )

    item_json = json.loads(item.model_dump_json())
    assert item_json["type"] == "items_custom"
    assert item_json["creator_ids"][0] == "0123456789ab0123456789ab"
    assert item_json["creator_ids"][1] == "1023456789ab0123456789ab"
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

    sample_dict = sample.model_dump()
    assert sample_dict["type"] == "samples"
    assert sample_dict["creator_ids"][0] == ObjectId("0123456789ab0123456789ab")
    assert sample_dict["creator_ids"][1] == ObjectId("1023456789ab0123456789ab")
    assert sample_dict["date"] == datetime.datetime.fromisoformat("2020-01-01 00:00").replace(
        tzinfo=datetime.timezone.utc
    )
    assert sample_dict["last_modified"] == datetime.datetime.fromisoformat(
        "2020-01-01 00:00"
    ).replace(tzinfo=datetime.timezone.utc)

    sample_json = json.loads(sample.model_dump_json())
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
        "111111111",
    ],
)
def test_good_ids(id):
    """Test good human-readable IDs for validity."""

    class TestModel(pydantic.BaseModel):
        test_id: HumanReadableIdentifier

    model = TestModel(test_id=id)
    assert model.test_id == id


@pytest.mark.parametrize(
    "id",
    [
        "MP2018(W/O)",
        "mp 1 2 3 4 5 6",
        "lithium & sodium",
        "me388-123456789-123456789-really-long-descriptive-identifier-that-should-be-the-name-but-is-otherwise-valid",
        111111111,
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

    class TestModel(pydantic.BaseModel):
        test_id: HumanReadableIdentifier

    with pytest.raises(pydantic.ValidationError):
        TestModel(test_id=id)


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

    cell = Cell(**json.loads(cell.model_dump_json()))
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


def test_cell_relationship_deduplication():
    """Regression test for duplicated parthood relationships.

    `entry_reference_lookup` enriches electrode constituents with their refcode
    at read time but does not back-fill the stored `relationships` rows. The
    dedup logic must therefore match a stored relationship that carries only an
    item_id against a constituent enriched with a refcode (and vice-versa),
    rather than appending a duplicate, and back-fill the missing identifier so
    the surviving relationship carries both.
    """
    from pydatalab.models.cells import Cell

    # Stored relationship has item_id only; constituent enriched with refcode.
    cell = Cell(
        item_id="abcd-1-2-3",
        positive_electrode=[
            {
                "item": {
                    "type": "samples",
                    "item_id": "test_cathode",
                    "refcode": "grey:ABCDEF",
                },
                "quantity": 1,
            }
        ],
        relationships=[
            {
                "relation": "is_part_of",
                "type": "samples",
                "item_id": "test_cathode",
                "description": "Is a constituent of",
            }
        ],
    )
    parthood = [r for r in cell.relationships if r.relation == RelationshipType.PARTHOOD]
    assert len(parthood) == 1
    # The refcode from the constituent is back-filled onto the stored relationship.
    assert parthood[0].refcode == "grey:ABCDEF"
    assert parthood[0].item_id == "test_cathode"

    # Reverse asymmetry: stored relationship has refcode, constituent item_id only.
    cell = Cell(
        item_id="abcd-1-2-3",
        positive_electrode=[
            {"item": {"type": "samples", "item_id": "test_cathode"}, "quantity": 1}
        ],
        relationships=[
            {
                "relation": "is_part_of",
                "type": "samples",
                "item_id": "test_cathode",
                "refcode": "grey:ABCDEF",
                "description": "Is a constituent of",
            }
        ],
    )
    parthood = [r for r in cell.relationships if r.relation == RelationshipType.PARTHOOD]
    assert len(parthood) == 1
    # The item_id from the constituent is back-filled onto the stored relationship.
    assert parthood[0].refcode == "grey:ABCDEF"
    assert parthood[0].item_id == "test_cathode"

    # Re-validating an already-clean cell must not grow the relationships list.
    cell = Cell(**json.loads(cell.model_dump_json()))
    parthood = [r for r in cell.relationships if r.relation == RelationshipType.PARTHOOD]
    assert len(parthood) == 1
    assert parthood[0].refcode == "grey:ABCDEF"
    assert parthood[0].item_id == "test_cathode"

    # Two constituents referencing the same entry (with a shared identifier) within
    # a single pass must collapse to one relationship, not append a duplicate.
    cell = Cell(
        item_id="abcd-1-2-3",
        positive_electrode=[
            {"item": {"type": "samples", "item_id": "test_cathode"}, "quantity": 1},
            {
                "item": {
                    "type": "samples",
                    "item_id": "test_cathode",
                    "refcode": "grey:ABCDEF",
                },
                "quantity": 1,
            },
        ],
    )
    parthood = [r for r in cell.relationships if r.relation == RelationshipType.PARTHOOD]
    assert len(parthood) == 1
    assert parthood[0].refcode == "grey:ABCDEF"
    assert parthood[0].item_id == "test_cathode"


def test_cell_nominal_capacity():
    """`nominal_capacity` is derived from `theoretical_capacity` (mAh/g) *
    `characteristic_mass` (mg) and is always held in its canonical unit (mAh);
    `nominal_capacity_unit` only records the unit it is displayed in."""
    from pydatalab.models.cells import Cell

    # Neither input supplied: no capacity can be computed.
    cell = Cell(item_id="abcd-1-2-3")
    assert cell.nominal_capacity is None

    # Only one of the two inputs supplied: still no capacity can be computed.
    cell = Cell(item_id="abcd-1-2-3", theoretical_capacity=200.0)
    assert cell.nominal_capacity is None

    cell = Cell(item_id="abcd-1-2-3", characteristic_mass=5.0)
    assert cell.nominal_capacity is None

    # Default unit (mAh): 200 mAh/g * 5 mg = 1 mAh.
    cell = Cell(item_id="abcd-1-2-3", characteristic_mass=5.0, theoretical_capacity=200.0)
    assert cell.nominal_capacity_unit == "mAh"
    assert cell.nominal_capacity == pytest.approx(1.0)

    # Displaying the result in Ah does not change the canonical (mAh) value.
    cell = Cell(
        item_id="abcd-1-2-3",
        characteristic_mass=5.0,
        theoretical_capacity=200.0,
        nominal_capacity_unit="Ah",
    )
    assert cell.nominal_capacity_unit == "Ah"
    assert cell.nominal_capacity == pytest.approx(1.0)

    # An explicitly unset nominal_capacity is computed, just like a missing one.
    cell = Cell(
        item_id="abcd-1-2-3",
        characteristic_mass=5.0,
        theoretical_capacity=200.0,
        nominal_capacity=None,
    )
    assert cell.nominal_capacity == pytest.approx(1.0)

    # Round-tripping through JSON (as happens on save/load) preserves the computed values.
    cell = Cell(**json.loads(cell.model_dump_json()))
    assert cell.nominal_capacity == pytest.approx(1.0)


def test_cell_nominal_capacity_provided_value_is_kept():
    """A provided `nominal_capacity` is never overwritten by the value computed from
    `theoretical_capacity` and `characteristic_mass`; whether it overrides that
    calculation is determined by comparing the two, not by a separate flag."""
    from pydatalab.models.cells import Cell

    # A provided value is honoured even though mass/theoretical capacity would imply
    # a different result.
    cell = Cell(
        item_id="abcd-1-2-3",
        characteristic_mass=5.0,
        theoretical_capacity=200.0,
        nominal_capacity=5.0,
    )
    assert cell.nominal_capacity == pytest.approx(5.0)

    # The display unit is a presentation preference: a provided value is canonical
    # (mAh) and is not rescaled by it.
    cell = Cell(
        item_id="abcd-1-2-3",
        nominal_capacity=5000.0,
        nominal_capacity_unit="Ah",
    )
    assert cell.nominal_capacity == pytest.approx(5000.0)
    assert cell.nominal_capacity_unit == "Ah"

    # Round-tripping through JSON preserves the provided value rather than recomputing it.
    cell = Cell(
        item_id="abcd-1-2-3",
        characteristic_mass=5.0,
        theoretical_capacity=200.0,
        nominal_capacity=5.0,
    )
    cell = Cell(**json.loads(cell.model_dump_json()))
    assert cell.nominal_capacity == pytest.approx(5.0)

    # Once computed, the value counts as provided: it is not recomputed when the
    # inputs later change, until it is unset again.
    cell = Cell(item_id="abcd-1-2-3", characteristic_mass=5.0, theoretical_capacity=200.0)
    stored = json.loads(cell.model_dump_json())
    cell = Cell(**{**stored, "characteristic_mass": 10.0})
    assert cell.nominal_capacity == pytest.approx(1.0)
    cell = Cell(**{**stored, "characteristic_mass": 10.0, "nominal_capacity": None})
    assert cell.nominal_capacity == pytest.approx(2.0)

    # Documents saved with the removed `nominal_capacity_manual` flag still load.
    cell = Cell(item_id="abcd-1-2-3", nominal_capacity=5.0, nominal_capacity_manual=True)
    assert cell.nominal_capacity == pytest.approx(5.0)
    assert "nominal_capacity_manual" not in cell.model_dump()


def test_cell_nominal_capacity_quantity_hints():
    """`nominal_capacity` declares its canonical unit and display-unit conversions via
    the `datalab_quantity` schema hint, with `nominal_capacity_unit` as its companion
    display-unit field."""
    from pydatalab.models.cells import Cell
    from pydatalab.models.schema_hints import validate_schema_hints
    from pydatalab.models.units import DatalabQuantity

    validate_schema_hints(Cell)

    properties = Cell.model_json_schema(by_alias=False)["properties"]
    quantity = DatalabQuantity(**properties["nominal_capacity"]["datalab_quantity"])
    assert quantity.canonical_unit == "mAh"
    assert quantity.display_unit_field == "nominal_capacity_unit"
    assert set(quantity.display_units) == set(properties["nominal_capacity_unit"]["enum"])

    # canonical = displayed * scale + offset
    assert quantity.display_units["mAh"].scale == pytest.approx(1.0)
    assert quantity.display_units["Ah"].scale == pytest.approx(1000.0)
    assert all(transform.offset == 0 for transform in quantity.display_units.values())

    # The canonical value is the only capacity field: there is no separate
    # unit-normalized copy to keep in sync, nor a flag recording where it came from.
    assert "nominal_capacity_mah" not in properties
    assert "nominal_capacity_manual" not in properties


def test_unit_bearing_fields_declare_quantities():
    """Built-in numeric fields with a fixed unit declare it via the `datalab_quantity`
    schema hint. Only `nominal_capacity` persists a display unit; for the others the
    display unit is not stored and values are converted on display."""
    from pydatalab.models.cells import Cell
    from pydatalab.models.samples import Sample
    from pydatalab.models.starting_materials import StartingMaterial
    from pydatalab.models.units import DatalabQuantity

    def quantities(model):
        properties = model.model_json_schema(by_alias=False)["properties"]
        return {
            name: DatalabQuantity(**prop["datalab_quantity"])
            for name, prop in properties.items()
            if "datalab_quantity" in prop
        }

    cell = quantities(Cell)
    assert {name: quantity.canonical_unit for name, quantity in cell.items()} == {
        "characteristic_mass": "mg",
        "characteristic_molar_mass": "g/mol",
        "theoretical_capacity": "mAh/g",
        "nominal_capacity": "mAh",
    }
    assert cell["characteristic_mass"].display_units["g"].scale == pytest.approx(1000.0)
    assert {name for name, quantity in cell.items() if quantity.display_unit_field} == {
        "nominal_capacity"
    }

    for model in (Sample, StartingMaterial):
        molar_mass = quantities(model)["molar_mass"]
        assert molar_mass.canonical_unit == "g/mol"
        assert molar_mass.display_unit_field is None

    # The hints are metadata only: values are still read and stored in the canonical unit.
    cell = Cell(item_id="abcd-1-2-3", characteristic_mass=5.0, theoretical_capacity=200.0)
    assert cell.characteristic_mass == 5.0
    assert cell.nominal_capacity == pytest.approx(1.0)


def test_datalab_quantity_display_units_default_to_canonical_unit():
    """`display_units` may be omitted for a field only displayed in its canonical unit."""
    from pydatalab.models.units import DatalabQuantity

    quantity = DatalabQuantity(canonical_unit="g/mol")
    assert set(quantity.display_units) == {"g/mol"}
    assert quantity.display_units["g/mol"].scale == 1.0
    assert quantity.display_units["g/mol"].offset == 0.0

    # When display units are given, they must still include the canonical unit.
    with pytest.raises(pydantic.ValidationError, match="canonical_unit must be present"):
        DatalabQuantity(canonical_unit="g", display_units={"mg": {"scale": 0.001}})


def test_example_custom_models_declare_quantities_without_display_unit_fields():
    """A quantity may omit `display_unit_field`, in which case no companion field is
    needed and the display unit is not stored with the item."""
    from pydatalab.models._example_custom import MyItem, MySample
    from pydatalab.models.schema_hints import validate_schema_hints
    from pydatalab.models.units import DatalabQuantity

    for model in (MySample, MyItem):
        validate_schema_hints(model)

    sample_properties = MySample.model_json_schema(by_alias=False)["properties"]
    drying_time = DatalabQuantity(**sample_properties["drying_time"]["datalab_quantity"])
    assert drying_time.canonical_unit == "h"
    assert drying_time.display_unit_field is None
    assert drying_time.display_units["min"].scale == pytest.approx(1 / 60)
    # Other hints on the same field are unaffected.
    assert sample_properties["drying_time"]["datalab_include_field_in_summary"] is True

    item_properties = MyItem.model_json_schema(by_alias=False)["properties"]
    for name in ("width", "height"):
        quantity = DatalabQuantity(**item_properties[name]["datalab_quantity"])
        assert quantity.canonical_unit == "mm"
        assert quantity.display_units["cm"].scale == pytest.approx(10.0)
    assert not any(name.endswith("_unit") for name in item_properties)


def test_sample_synthesis_relationship_deduplication():
    """Regression test for duplicated parent relationships on synthesis constituents.

    Mirrors `test_cell_relationship_deduplication` for the
    `add_missing_synthesis_relationships` validator: a stored relationship that
    carries only one identifier must match a constituent enriched with the other
    (in either direction), back-fill the missing identifier rather than appending
    a duplicate, and remain idempotent on re-validation.
    """
    from pydatalab.models.samples import Sample

    # Stored relationship has item_id only; constituent enriched with refcode.
    sample = Sample(
        item_id="abcd-1-2-3",
        synthesis_constituents=[
            {
                "item": {
                    "type": "starting_materials",
                    "item_id": "sm_1",
                    "refcode": "grey:ABCDEF",
                },
                "quantity": 1,
            }
        ],
        relationships=[
            {
                "relation": "parent",
                "type": "starting_materials",
                "item_id": "sm_1",
                "description": "Is a constituent of",
            }
        ],
    )
    parents = [r for r in sample.relationships if r.relation == RelationshipType.PARENT]
    assert len(parents) == 1
    assert parents[0].refcode == "grey:ABCDEF"
    assert parents[0].item_id == "sm_1"

    # Reverse asymmetry: stored relationship has refcode *only*; the constituent
    # supplies the item_id, which must be back-filled onto the matched relationship.
    sample = Sample(
        item_id="abcd-1-2-3",
        synthesis_constituents=[
            {
                "item": {
                    "type": "starting_materials",
                    "item_id": "sm_1",
                    "refcode": "grey:ABCDEF",
                },
                "quantity": 1,
            }
        ],
        relationships=[
            {
                "relation": "parent",
                "type": "starting_materials",
                "refcode": "grey:ABCDEF",
                "description": "Is a constituent of",
            }
        ],
    )
    parents = [r for r in sample.relationships if r.relation == RelationshipType.PARENT]
    assert len(parents) == 1
    assert parents[0].refcode == "grey:ABCDEF"
    assert parents[0].item_id == "sm_1"

    # Re-validating an already-clean sample must not grow the relationships list.
    sample = Sample(**json.loads(sample.model_dump_json()))
    parents = [r for r in sample.relationships if r.relation == RelationshipType.PARENT]
    assert len(parents) == 1
    assert parents[0].refcode == "grey:ABCDEF"
    assert parents[0].item_id == "sm_1"


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

    class TestModel(pydantic.BaseModel):
        test_refcode: Refcode

    with pytest.raises(pydantic.ValidationError):
        TestModel(test_refcode=refcode)


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

    class TestModel(pydantic.BaseModel):
        name: DisplayName

    assert TestModel(name=display_name)


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

    class TestModel(pydantic.BaseModel):
        name: DisplayName

    with pytest.raises(ValueError):
        TestModel(name=display_name)


@pytest.mark.parametrize(
    "contact_email",
    [
        "test@example.com",
    ],
)
def test_good_email(contact_email):

    class TestModel(pydantic.BaseModel):
        email: EmailStr

    assert TestModel(email=contact_email)


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

    class TestModel(pydantic.BaseModel):
        email: EmailStr

    with pytest.raises(ValueError):
        TestModel(email=contact_email)


def test_builtin_models_have_valid_schema_hints():
    """Every built-in item model's datalab schema hints validate against the
    DatalabFieldExtra/DatalabModelExtra vocabulary."""
    from pydatalab.models.schema_hints import validate_schema_hints

    for model in ITEM_MODELS.values():
        validate_schema_hints(model)


def test_datalab_field_extra_rejects_unknown_and_mistyped_hints():
    from pydatalab.models.schema_hints import DatalabFieldExtra
    from pydatalab.models.units import DatalabQuantity

    # Unknown datalab_ key.
    with pytest.raises(pydantic.ValidationError):
        DatalabFieldExtra(datalab_include_in_summary=True)

    # Wrong type for a known key.
    with pytest.raises(pydantic.ValidationError):
        DatalabFieldExtra(datalab_ref_types="equipment")

    # A valid set of hints passes.
    quantity = DatalabQuantity(
        canonical_unit="V",
        display_units={
            "V": {"scale": 1},
            "mV": {"scale": 0.001},
        },
        default_display_unit="mV",
    )
    field_extra = DatalabFieldExtra(
        datalab_include_field_in_summary=True,
        datalab_ref_types=["equipment"],
        datalab_quantity=quantity,
    )
    assert field_extra.datalab_quantity == quantity


def test_validate_schema_hints_checks_canonical_quantity_relationship():
    from typing import Literal

    from pydantic import Field

    from pydatalab.models.schema_hints import validate_schema_hints
    from pydatalab.models.utils import BaseModel

    class _QuantityModel(BaseModel):
        volume: float | None = Field(
            None,
            json_schema_extra={
                "datalab_quantity": {
                    "canonical_unit": "L",
                    "display_units": {
                        "L": {"scale": 1},
                        "mL": {"scale": 0.001},
                    },
                    "default_display_unit": "mL",
                    "display_unit_field": "volume_display_unit",
                }
            },
        )
        volume_display_unit: Literal["L", "mL"] | None = None

    validate_schema_hints(_QuantityModel)

    class _MismatchedUnits(BaseModel):
        volume: float | None = Field(
            None,
            json_schema_extra=_QuantityModel.model_fields["volume"].json_schema_extra,
        )
        volume_display_unit: Literal["L", "cL"] | None = None

    with pytest.raises(ValueError, match="containing exactly"):
        validate_schema_hints(_MismatchedUnits)


def test_validate_schema_hints_raises_for_bad_field_hint():
    from pydantic import Field

    from pydatalab.models.schema_hints import validate_schema_hints
    from pydatalab.models.utils import BaseModel

    class _BadHints(BaseModel):
        # `datalab_multlinee` is a typo of `datalab_multiline`.
        widget: str | None = Field(None, json_schema_extra={"datalab_multlinee": True})

    with pytest.raises(ValueError, match="widget"):
        validate_schema_hints(_BadHints)

    class _InvalidExtra(BaseModel):
        widget: str | None = Field(None, json_schema_extra="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="expected a dict, callable, or None"):
        validate_schema_hints(_InvalidExtra)
