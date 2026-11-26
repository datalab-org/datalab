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

    @model_validator(mode="before")
    @classmethod
    def remove_field_relationships(cls, data):
        """Remove the relationships that belong to the fields carrying a
        `datalab_relationship` hint, so that `add_field_relationships` rebuilds them from
        the current content of these fields.

        A relationship belongs to a field when it has the `relation` and `description`
        of the field's hint.
        """
        from pydatalab.models.schema_hints import relationship_hints

        hints = relationship_hints(cls)
        if not hints or not isinstance(data, dict) or not data.get("relationships"):
            return data

        owned = {(hint.relation, hint.description) for hint in hints.values()}

        def _key(relationship):
            if isinstance(relationship, dict):
                return relationship.get("relation"), relationship.get("description")
            return (
                getattr(relationship, "relation", None),
                getattr(relationship, "description", None),
            )

        return {
            **data,
            "relationships": [rel for rel in data["relationships"] if _key(rel) not in owned],
        }

    @model_validator(mode="after")
    def add_field_relationships(self):
        """Add a relationship for every item referenced, at any depth, in a field carrying
        a `datalab_relationship` hint, with the `relation` and `description` of the hint.

        The relationships of these fields are removed before validation (see
        `remove_field_relationships`) and added again here, so clearing a reference also
        removes its relationship. Other relationships are left untouched.
        """
        from pydatalab.models.relationships import TypedRelationship
        from pydatalab.models.schema_hints import relationship_hints

        added: dict[tuple, set[str]] = {}
        for field, hint in relationship_hints(type(self)).items():
            identifiers = added.setdefault((hint.relation, hint.description), set())
            for reference in iter_item_references(getattr(self, field)):
                refcode = reference.refcode
                item_id = reference.item_id
                if not (refcode or item_id):
                    raise ValueError(
                        f"References to items in {field!r} must provide a `refcode` or an "
                        f"`item_id`, not only an `immutable_id`: {reference!r}"
                    )
                if refcode in identifiers or item_id in identifiers:
                    continue
                identifiers.update(i for i in (refcode, item_id) if i)
                self.relationships.append(
                    TypedRelationship(
                        relation=hint.relation,
                        refcode=refcode,
                        item_id=item_id,
                        type=reference.type,
                        description=hint.description,
                    )
                )

        return self
