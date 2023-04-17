import abc
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator

# from pydatalab.models.entries import Entry, EntryReference
from pydatalab.models.people import Person
from pydatalab.models.utils import (  # PyObjectId,; Refcode,
    JSON_ENCODERS,
    HumanReadableIdentifier,
    IsoformatDateTime,
    KnownType,
)


class RelationshipType(str, Enum):
    """An enumeration of the possible types of relationship between two entries.

    ```mermaid
    classDiagram
    class entryC
    entryC --|> entryA: parent
    entryC ..|> entryD
    entryA <..> entryD: sibling
    entryA --|> entryB : child
    ```

    """

    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    PARTHOOD = "is_part_of"
    OTHER = "other"


class TypedRelationship(BaseModel):
    # description: Optional[str] = Field(
    #     None,
    #     description="A description of the relationship.",
    # )

    relation: RelationshipType = Field(
        description="The type of relationship between the two items. If the type is 'other', then a human-readable description should be provided."
    )

    type: KnownType = Field(description="The type of the related resource.")

    # immutable_id: Optional[PyObjectId] = Field(
    #     description="The immutable ID of the entry that is related to this entry."
    # )

    item_id: Optional[HumanReadableIdentifier] = Field(
        description="The ID of the entry that is related to this entry."
    )

    # refcode: Optional[Refcode] = Field(
    #     description="The refcode of the entry that is related to this entry."
    # )


class Entry(BaseModel, abc.ABC):
    """An Entry is an abstract base class for any model that can be
    deserialized and stored in the database.

    """

    type: str
    """The resource type of the entry."""

    # immutable_id: PyObjectId = Field(
    #     None,
    #     title="Immutable ID",
    #     alias="_id",
    # )
    """The immutable database ID of the entry."""

    # last_modified: Optional[IsoformatDateTime] = None
    # """The timestamp at which the entry was last modified."""

    relationships: Optional[List[TypedRelationship]] = None
    """A list of related entries and their types."""

    # revision: int = 1
    # """The revision number of the entry."""

    # revisions: Optional[Dict[int, Any]] = None
    # """An optional mapping from old revision numbers to the model state at that revision."""

    class Config:
        allow_population_by_field_name = True
        json_encoders = JSON_ENCODERS
        extra = "ignore"


class EntryReference(BaseModel):
    """A reference to a database entry by ID and type.

    Can include additional arbitarary metadata useful for
    inlining the item data.

    """

    type: str
    # immutable_id: Optional[PyObjectId]
    item_id: Optional[HumanReadableIdentifier]
    # refcode: Optional[Refcode]
    name: Optional[str]

    class Config:
        extra = "ignore"


class File(BaseModel):
    """A model for representing a file that has been tracked or uploaded to datalab."""

    name: str = Field(description="The filename on disk.")
    """the name of the file"""

    # size: Optional[int] = Field(description="The size of the file on disk in bytes.")

    # last_modified_remote: Optional[IsoformatDateTime] = Field(
    #     description="The last date/time at which the remote file was modified."
    # )

    # item_ids: List[str] = Field(description="A list of item IDs associated with this file.")

    # blocks: List[str] = Field(description="A list of block IDs associated with this file.")

    extension: str = Field(description="The file extension that the file was uploaded with.")
    """the file extension"""

    # original_name: Optional[str] = Field(description="The raw filename as uploaded.")

    # location: Optional[str] = Field(description="The location of the file on disk.")

    # url_path: Optional[str] = Field(description="The path to a remote file.")

    # source: Optional[str] = Field(
    #     description="The source of the file, e.g. 'remote' or 'uploaded'."
    # )

    # time_added: datetime.datetime = Field(description="The timestamp for the original file upload.")

    # metadata: Optional[Dict[Any, Any]] = Field(description="Any additional metadata.")

    # representation: Optional[Any] = Field()

    # source_server_name: Optional[str] = Field(
    #     description="The server name at which the file is stored."
    # )

    # source_path: Optional[str] = Field(description="The path to the file on the remote resource.")

    # is_live: bool = Field(
    #     description="Whether or not the file should be watched for future updates."
    # )


class Block(BaseModel):
    blocktype: str

    title: str

    freeform_comment: Optional[str]

    # file_id: PyObjectId


class Item(Entry, abc.ABC):
    """The generic model for data types that will be exposed with their own named endpoints."""

    # refcode: Refcode = None  # type: ignore
    # """A globally unique immutable ID comprised of the deployment prefix (e.g., `grey`)
    # and a locally unique string, ideally created with some consistent scheme.
    # """

    item_id: HumanReadableIdentifier
    """A locally unique, human-readable identifier for the entry. This ID is mutable."""

    # creator_ids: List[PyObjectId] = Field([])
    # """The database IDs of the user(s) who created the item."""

    creators: Optional[List[Person]] = Field(None)
    """Inlined info for the people associated with this item."""

    description: Optional[str]
    """A description of the item, either in plain-text or a markup language."""

    date: Optional[IsoformatDateTime]
    """A relevant 'creation' timestamp for the entry (e.g., purchase date, synthesis date)."""

    name: Optional[str]
    """An optional human-readable/usable name for the entry."""

    blocks_obj: Dict[str, Block]
    """A mapping from block ID to block data."""

    # display_order: List[str] = Field([])
    # """The order in which to display block data in the UI."""

    files: Optional[List[File]]
    """Any files attached to this sample."""

    # file_ObjectIds: List[PyObjectId] = Field([])
    """Links to object IDs of files stored within the database."""

    # @validator("refcode", pre=True, always=True)
    # def refcode_validator(cls, v):
    #     """Generate a refcode if not provided; check that the refcode has the correct prefix if provided."""

    #     from pydatalab.config import CONFIG

    #     if v and not v.startswith(f"{CONFIG.IDENTIFIER_PREFIX}:"):
    #         raise ValueError(f"refcode missing prefix {CONFIG.IDENTIFIER_PREFIX!r}")

    #     return v


class Constituent(BaseModel):
    """A constituent of a sample."""

    item: EntryReference = Field(...)
    """A reference to item (sample or starting material) entry for the constituent substance."""

    quantity: Optional[float] = Field(..., ge=0, exclude=True)
    """The amount of the constituent material used to create the sample."""

    unit: str = Field("g", exclude=True)
    """The unit symbol for the value provided in `quantity`, default is mass
    in grams (g) but could also refer to volumes (mL, L, etc.) or moles (mol).
    """

    quantity_with_units: Optional[str] = ""

    @validator("quantity_with_units", pre=True, always=True)
    def concat_quantity_and_units(cls, v, values):
        """create a formatted string with the quantity and unit"""

        quantity = values.get("quantity")
        unit = values.get("unit")
        # if not v:
        v = f"{quantity} {unit}"
        return v


class Sample(Item):
    """A model for representing an experimental sample."""

    type: str = Field("samples", const="samples", pattern="^samples$")

    chemical_formula: Optional[str] = Field(example=["Na3P", "LiNiO2@C"], alias="chemform")
    """A string representation of the chemical formula or composition associated with this sample."""

    synthesis_constituents: List[Constituent] = Field([])
    """A list of references to constituent materials giving the amount and relevant inlined details of consituent items."""

    synthesis_description: Optional[str]
    """Free-text details of the procedure applied to synthesise the sample"""


class CellFormat(str, Enum):
    coin = "coin"
    pouch = "pouch"
    in_situ_xrd = "in situ (XRD)"
    in_situ_nmr = "in situ (NMR)"
    in_situ_squid = "in situ (SQUID)"
    swagelok = "swagelok"
    cylindrical = "cylindrical"
    other = "other"


class InlineSubstance(BaseModel):
    name: str
    chemform: Optional[str]


class CellComponent(Constituent):
    """A constituent of a sample."""

    item: Union[EntryReference, InlineSubstance]
    """A reference to item (sample or starting material) entry for the constituent substance."""

    # @validator("item", pre=True, always=True)
    # def coerce_reference3(cls, v):
    #     if isinstance(v, dict):
    #         id = v.pop("item_id", None)
    #         if id:
    #             return EntryReference(item_id=id, **v)
    #         else:
    #             name = v.pop("name", "")
    #             chemform = v.pop("chemform", None)
    #             if not name:
    #                 raise ValueError("Inline substance must have a name!")
    #             return InlineSubstance(name=name, chemform=chemform)
    #     return v


class Cell(Item):
    """A model for representing electrochemical cells."""

    type: str = Field("cells", const="cells", pattern="^cells$")

    cell_format: Optional[CellFormat] = Field(
        description="The form factor of the cell, e.g., coin, pouch, in situ or otherwise.",
    )

    cell_format_description: Optional[str] = Field(
        description="Additional human-readable description of the cell form factor, e.g., 18650, AMPIX, CAMPIX"
    )

    cell_preparation_description: Optional[str] = Field()

    characteristic_mass: Optional[float] = Field(
        description="The characteristic mass of the cell in milligrams. Can be used to normalize capacities."
    )

    characteristic_chemical_formula: Optional[str] = Field(
        description="The chemical formula of the active material. Can be used to calculated molar mass in g/mol for normalizing capacities."
    )

    characteristic_molar_mass: Optional[float] = Field(
        description="The molar mass of the active material, in g/mol. Will be inferred from the chemical formula, or can be supplied if it cannot be supplied"
    )

    positive_electrode: List[CellComponent] = Field([])

    negative_electrode: List[CellComponent] = Field([])

    electrolyte: List[CellComponent] = Field([])

    active_ion_charge: float = Field(1)

    @validator("cell_format", "cell_format_description")
    def check_descriptions_for_ambiguous_formats(cls, v, values):
        if (
            values.get("cell_format") == CellFormat.other
            and values.get("cell_format_description") is None
        ):
            raise ValueError("cell_format_description must be set if cell_format is 'other'")

        return v

    @validator("characteristic_molar_mass", always=True, pre=True)
    def set_molar_mass2(cls, v, values):
        from periodictable import formula

        if not v:
            chemical_formula = values.get("characteristic_chemical_formula")

            if chemical_formula:
                try:
                    return formula(chemical_formula).mass
                except Exception:
                    return None

        return v

    @root_validator
    def add_missing_electrode_relationships(cls, values):
        """Add any missing sample synthesis constituents to parent relationships"""
        from pydatalab.models.relationships import RelationshipType, TypedRelationship

        existing_parthood_relationship_ids = set()
        if values.get("relationships") is not None:
            existing_parthood_relationship_ids = set(
                relationship.item_id
                for relationship in values["relationships"]
                if relationship.relation == RelationshipType.PARTHOOD
            )
        else:
            values["relationships"] = []

        for component in ("positive_electrode", "negative_electrode", "electrolyte"):
            for constituent in values.get(component, []):
                if (
                    isinstance(constituent.item, EntryReference)
                    and constituent.item.item_id not in existing_parthood_relationship_ids
                ):
                    relationship = TypedRelationship(
                        relation=RelationshipType.PARTHOOD,
                        item_id=constituent.item.item_id,
                        type=constituent.item.type,
                        description="Is a constituent of",
                    )
                    values["relationships"].append(relationship)

        return values
