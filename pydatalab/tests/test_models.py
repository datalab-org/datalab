import pydantic
import pytest

from pydatalab.models import ITEM_MODELS
from pydatalab.models.relationships import (
    KnownType,
    RelationshipType,
    TypedRelationship,
)


def test_generate_schemas():
    """Test that all item model schemas can be generated."""
    for type in ITEM_MODELS:
        assert ITEM_MODELS[type].schema()


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
