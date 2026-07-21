from typing import Any

from pydantic import AliasChoices, ConfigDict, Field, field_validator, model_validator

from pydatalab.models.people import Group, Person
from pydatalab.models.utils import BaseModel, Constituent, InlineSubstance, PyObjectId

__all__ = (
    "HasOwner",
    "HasRevisionControl",
    "IsCollectable",
    "HasSynthesisInfo",
    "HasSubstanceInfo",
)


class HasOwner(BaseModel):
    creator_ids: list[PyObjectId] = Field([])
    """The database IDs of the user(s) who created the item."""

    creators: list[Person] | None = Field(None)
    """Inlined info for the people associated with this item."""

    group_ids: list[PyObjectId] = Field([])
    """The database IDs of the group(s) that have read-access to this item."""

    groups: list[Group] | None = Field(None)
    """Inlined info for the groups with access to this item."""


class HasRevisionControl(BaseModel):
    revision: int = 1
    """The revision number of the entry."""

    revisions: dict[int, Any] | None = None
    """An optional mapping from old revision numbers to the model state at that revision."""

    version: int = 1
    """The version number used by the version control system for tracking snapshots."""


class CollectionReference(BaseModel):
    """A reference to a collection, used for inlining collection info within other models."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    immutable_id: PyObjectId = Field(alias="_id")
    """The immutable ID of the collection."""


class IsCollectable(BaseModel):
    """Trait mixin for models that can be
    added to collections.
    """

    collections: list[CollectionReference] = Field(default_factory=list)
    """Inlined info for the collections associated with this item."""

    @model_validator(mode="after")
    def add_missing_collection_relationships(self):
        from pydatalab.models.relationships import TypedRelationship

        if self.collections is not None:
            new_ids = {coll.immutable_id for coll in self.collections}
            existing_collection_relationship_ids = {
                relationship.immutable_id
                for relationship in self.relationships
                if relationship.type == "collections"
            }

            for collection in self.collections:
                if collection.immutable_id not in existing_collection_relationship_ids:
                    relationship = TypedRelationship(
                        relation=None,
                        immutable_id=collection.immutable_id,
                        type="collections",
                        description="Is a member of",
                    )
                    self.relationships.append(relationship)

            self.relationships = [
                d
                for d in self.relationships
                if d.type != "collections" or d.immutable_id in new_ids
            ]

        if len([d for d in self.relationships if d.type == "collections"]) != len(self.collections):
            raise RuntimeError("Relationships and collections mismatch")

        return self


class HasSynthesisInfo(BaseModel):
    """Trait mixin for models that have synthesis information."""

    synthesis_constituents: list[Constituent] = Field([])
    """A list of references to constituent materials giving the amount and relevant inlined details of consituent items."""

    synthesis_description: str | None = None
    """Free-text details of the procedure applied to synthesise the sample"""

    @model_validator(mode="after")
    def add_missing_synthesis_relationships(self):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        constituents_set = set()
        if self.synthesis_constituents is not None:
            # Index by refcode *and* item_id so a stored relationship carrying an
            # item_id still matches a refcode-enriched constituent (and vice-versa).
            existing_parent_relationships = {
                identifier: relationship
                for relationship in self.relationships
                if relationship.relation == RelationshipType.PARENT
                for identifier in (relationship.refcode, relationship.item_id)
                if identifier
            }

            for constituent in self.synthesis_constituents:
                # If this is an inline relationship, just skip it
                if isinstance(constituent.item, InlineSubstance):
                    continue

                refcode = constituent.item.refcode
                item_id = constituent.item.item_id

                relationship = existing_parent_relationships.get(
                    refcode
                ) or existing_parent_relationships.get(item_id)
                if relationship is None:
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARENT,
                        refcode=refcode,
                        item_id=item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    self.relationships.append(relationship)
                else:
                    # Back-fill any identifier missing from the stored relationship
                    relationship.refcode = relationship.refcode or refcode
                    relationship.item_id = relationship.item_id or item_id

                # Register the relationship's identifiers in the index so a later
                # constituent referencing the same entry matches it rather than
                # appending a duplicate within this same validation pass.
                for identifier in (relationship.refcode, relationship.item_id):
                    if identifier:
                        existing_parent_relationships[identifier] = relationship

                # Accumulate all constituent IDs in a set to filter those that have been deleted
                constituents_set.update(i for i in (refcode, item_id) if i)

        # Finally, filter out any parent relationships with item that were removed
        # from the synthesis constituents
        self.relationships = [
            rel
            for rel in self.relationships
            if not (
                rel.refcode not in constituents_set
                and rel.item_id not in constituents_set
                and rel.relation == RelationshipType.PARENT
                and rel.type in ("samples", "starting_materials")
            )
        ]

        return self


class HasSubstanceInfo(BaseModel):
    """Trait mixin for models that have substance information."""

    chemform: str | None = Field(
        None,
        examples=["Na3P", "Na<sub>3</sub>P", "LiNiO2@C", "Na3+xP", "LiNi1/3Co0.1Mn0.1O2"],
    )
    """A string representation of the chemical formula or composition associated with this sample.

    The representation is relatively free-form; clients are expected parse and interpret HTML markup for subscripts
    and accept unicode characters for greek letters.

    """

    smiles: str | None = Field(
        None, validation_alias=AliasChoices("smiles_representation", "SMILES")
    )
    """A SMILES string representation of the chemical structure associated with this sample."""

    inchi: str | None = Field(None)
    """An International Chemical Identifier (InChI) string representation of chemicals/molecules associated with this sample."""

    inchi_key: str | None = Field(None)
    """A unique key derived from the InChI."""

    GHS_codes: str | None = Field(
        None,
        alias="GHS H-codes",
        examples=["H224", "H303, H316, H319"],
    )
    """A string describing any GHS hazard codes associated with this item. See https://pubchem.ncbi.nlm.nih.gov/ghs/ for code definitions."""

    molar_mass: float | None = Field(None, alias="Molecular Weight", validate_default=True)
    """Mass per formula unit, in g/mol."""

    CAS: str | None = Field(None, alias="Substance CAS")
    """The CAS Registry Number for the substance described by this entry."""

    @field_validator("molar_mass", mode="before")
    @classmethod
    def add_molar_mass(cls, v, info):
        """Fill in the molar mass if not already set and a chemical formula is provided."""
        from periodictable import formula

        chemform = info.data.get("chemform")
        if v is None and chemform:
            try:
                return formula(chemform).mass
            except Exception:
                return None

        return v
