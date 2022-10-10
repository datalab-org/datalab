import pydantic
import pytest

from pydatalab.models.relationships import (
    KnownType,
    RelationshipType,
    TypedRelationship,
)


def test_relationship_with_custom_type():
    """Test that a relationship with a custom type can be created."""
    relationship = TypedRelationship(
        relation=RelationshipType.OTHER,
        type=KnownType.SAMPLE,
        item_id="1234",
        description="This is a relationship",
    )
    assert relationship.relation == RelationshipType.OTHER
    assert relationship.type == KnownType.SAMPLE
    assert relationship.item_id == "1234"
    assert relationship.description == "This is a relationship"

    with pytest.raises(pydantic.ValidationError):
        relationship = TypedRelationship(
            relation=RelationshipType.OTHER, type=KnownType.SAMPLE, item_id="1234", description=None
        )
