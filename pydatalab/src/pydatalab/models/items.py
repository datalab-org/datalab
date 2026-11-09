import abc

from pydantic import Field, field_validator, model_validator

from pydatalab.models.blocks import HasBlocks
from pydatalab.models.entries import Entry
from pydatalab.models.files import HasFiles
from pydatalab.models.traits import (
    HasLocation,
    HasOwner,
    HasRevisionControl,
    HasTags,
    IsCollectable,
)
from pydatalab.models.utils import (
    HumanReadableIdentifier,
    IsoformatDateTime,
    Refcode,
    iter_item_references,
)


class Item(
    Entry,
    HasOwner,
    HasRevisionControl,
    IsCollectable,
    HasBlocks,
    HasLocation,
    HasFiles,
    HasTags,
    abc.ABC,
):
    """The generic model for data types that will be exposed with their own named endpoints.

    `Item` is the abstract base shared by every physical item type: samples, cells,
    starting materials and equipment. `item_id` is normally the only required field;
    the remaining fields are either optional metadata or bookkeeping that the server
    populates itself.
    """

    refcode: Refcode | None = Field(
        None,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """A globally unique immutable ID comprised of the deployment prefix (e.g., `grey`) and a locally unique string, ideally created with some consistent scheme."""

    item_id: HumanReadableIdentifier = Field(
        ...,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """A locally unique, human-readable identifier for the entry. This ID is mutable."""

    description: str | None = None
    """A description of the item, either in plain-text or a markup language."""

    date: IsoformatDateTime | None = Field(
        None,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: str | None = Field(
        None,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """An optional human-readable/usable name for the entry."""

    status: str | None = Field(
        None,
        json_schema_extra={"datalab_include_field_in_summary": True},
    )
    """The status of the item, with allowed values defined by the specific item class."""

    @field_validator("refcode", mode="before")
    @classmethod
    def refcode_validator(cls, v):
        """Generate a refcode if not provided."""

        if v:
            prefix = None
            id = None
            prefix, id = v.split(":")
            if prefix is None or id is None:
                raise ValueError(f"refcode missing prefix or ID {id=}, {prefix=} from {v=}")

        return v

    @model_validator(mode="after")
    def add_missing_reference_relationships(self):
        """Add a parent relationship for every item referenced in a custom field (see
        `custom_item_fields`), and remove parent relationships to items that are no
        longer referenced. Built-in types are left untouched."""
        from pydatalab.models import custom_item_fields
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        fields = custom_item_fields(self.type)
        if not fields:
            return self

        references = list(iter_item_references([getattr(self, field) for field in fields]))

        # Index by refcode *and* item_id so a stored relationship carrying an
        # item_id still matches a refcode-enriched reference (and vice-versa).
        existing_relationships = {
            identifier: relationship
            for relationship in self.relationships
            if relationship.relation == RelationshipType.PARENT
            for identifier in (relationship.refcode, relationship.item_id)
            if identifier
        }

        for reference in references:
            refcode = reference.refcode
            item_id = reference.item_id
            if not (refcode or item_id):
                continue

            relationship = existing_relationships.get(refcode) or existing_relationships.get(
                item_id
            )
            if relationship is None:
                relationship = TypedRelationship(
                    relation=RelationshipType.PARENT,
                    refcode=refcode,
                    item_id=item_id,
                    type=reference.type,
                    description="Is referenced by",
                )
                self.relationships.append(relationship)
            else:
                relationship.refcode = relationship.refcode or refcode
                relationship.item_id = relationship.item_id or item_id

            for identifier in (relationship.refcode, relationship.item_id):
                if identifier:
                    existing_relationships[identifier] = relationship

        # Rebuild the list without the parent relationships to items that are no longer
        # referenced, so that clearing a reference field also removes its relationship.
        # As in `HasSynthesisInfo.add_missing_synthesis_relationships`, relationships do
        # not record which field created them: any parent relationship that is neither
        # referenced by a custom field nor by a synthesis constituent is removed.
        # Synthesis constituents are counted as references so that their parent
        # relationships, managed by `HasSynthesisInfo`, are kept.
        references.extend(iter_item_references(getattr(self, "synthesis_constituents", [])))
        referenced = {
            identifier
            for reference in references
            for identifier in (reference.refcode, reference.item_id)
            if identifier
        }
        self.relationships = [
            rel
            for rel in self.relationships
            if not (
                rel.relation == RelationshipType.PARENT
                and rel.refcode not in referenced
                and rel.item_id not in referenced
            )
        ]

        return self
