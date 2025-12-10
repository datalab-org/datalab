import datetime
import random
import string
from collections.abc import Callable
from enum import Enum
from functools import partial
from typing import TypeAlias

import pint
from bson.objectid import ObjectId
from pydantic import (
    BaseModel,
    ConstrainedStr,
    Field,
    parse_obj_as,
    root_validator,
    validator,
)


class ItemType(str, Enum):
    """An enumeration of the types of items known by this implementation, should be made dynamic in the future."""

    SAMPLES = "samples"
    STARTING_MATERIALS = "starting_materials"


class ItemStatus(str, Enum):
    """An enumeration of the status of items"""

    ACTIVE = "active"
    PLANNED = "planned"
    DISPOSED = "disposed"
    COMPLETED = "completed"
    FAILED = "failed"
    OTHER = "other"


SampleStatus = ItemStatus
"""An enumeration of the status of samples"""


class CellStatus(str, Enum):
    """An enumeration of the status of cells"""

    ACTIVE = "active"
    PLANNED = "planned"
    DISPOSED = "disposed"
    CYCLED = "cycled"
    SHORTED = "shorted"
    DISMANTLED = "dismantled"
    OTHER = "other"


class EquipmentStatus(str, Enum):
    """An enumeration of the status of equipments"""

    WORKING = "working"
    BROKEN = "broken"
    BEING_FIXED = "being_fixed"
    DEFUNCT = "defunct"
    NOT_BEING_FIXED = "not_being_fixed"
    OTHER = "other"


class StartingMaterialsStatus(str, Enum):
    """An enumeration of the status of starting materials"""

    ORDERED = "ordered"
    DISPOSED = "disposed"
    PLANNED = "planned"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    EXHAUSTED = "exhausted"
    OTHER = "other"


class KnownType(str, Enum):
    """An enumeration of the types of entry known by this implementation, should be made dynamic in the future."""

    SAMPLES = "samples"
    STARTING_MATERIALS = "starting_materials"
    BLOCKS = "blocks"
    FILES = "files"
    PEOPLE = "people"
    COLLECTIONS = "collections"


IDENTIFIER_REGEX = r"^(?:[a-zA-Z0-9]+|[a-zA-Z0-9][a-zA-Z0-9._-]+[a-zA-Z0-9])$"
"""A regex that matches identifiers that are url-safe and do not contain
leading or trailing punctuation.
"""


class HumanReadableIdentifier(ConstrainedStr):
    """Used to constrain human-readable and URL-safe identifiers for items."""

    min_length = 1
    max_length = 40
    strip_whitespace = True
    to_lower = False
    strict = False
    regex = IDENTIFIER_REGEX

    def __init__(self, value):
        self.value = parse_obj_as(type(self), value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __bool__(self):
        return bool(self.value)


class Refcode(HumanReadableIdentifier):
    regex = r"^[a-z]{2,10}:" + IDENTIFIER_REGEX[1:]
    """A regex to match refcodes that have a lower-case prefix between 2-10 chars, followed by a colon,
    and then the normal rules for an ID (url-safe etc.).

    """

    @property
    def prefix(self):
        return self.value.split(":")[0]

    @property
    def identifier(self):
        return self.value.split(":")[1]


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


class PintType(str):
    """A WIP attempt to create a custom pydantic field type for Pint quantities.
    The idea would eventually be to use TypeAlias to create physical/dimensionful pydantic fields.

    """

    Q = pint.Quantity

    def __init__(self, dimensions: str):
        self._dimensions = dimensions

    @classmethod
    def __get_validators__(self):
        yield self.validate

    @classmethod
    def validate(self, v):
        q = self.Q(v)
        if not q.check(self._dimensions):
            raise ValueError("Value {v} must have dimensions of mass, not {v.dimensions}")
        return q

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


Mass: TypeAlias = PintType("[mass]")  # type: ignore # noqa
Volume: TypeAlias = PintType("[volume]")  # type: ignore # noqa


class PyObjectId(ObjectId):
    """A wrapper class for a BSON ObjectId that can be used as a Pydantic field type.

    Modified from "Getting started iwth MongoDB and FastAPI":
    https://www.mongodb.com/developer/languages/python/python-quickstart-fastapi/.

    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict) and "$oid" in v:
            v = v["$oid"]

        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")

        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class IsoformatDateTime(datetime.datetime):
    """A datetime container that is more flexible than the pydantic default."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v) -> datetime.datetime | None:
        """Cast isoformat strings to datetimes and enforce UTC if tzinfo is missing."""
        if isinstance(v, str):
            if v in ["0", " "]:
                return None
            v = datetime.datetime.fromisoformat(v)

        if v.tzinfo is None:
            v = v.replace(tzinfo=datetime.timezone.utc)

        return v


JSON_ENCODERS = {
    pint.Quantity: str,
    ObjectId: str,
}


class RefCodeFactory:
    refcode_generator: Callable

    @classmethod
    def generate(self):
        from pydatalab.config import CONFIG

        return f"{CONFIG.IDENTIFIER_PREFIX}:{self.refcode_generator()}"


def random_uppercase(length: int = 6):
    return "".join(random.choices(string.ascii_uppercase, k=length))  # noqa: S311


class RandomAlphabeticalRefcodeFactory(RefCodeFactory):
    refcode_generator = partial(random_uppercase, length=6)


def generate_unique_refcode():
    """Generates a unique refcode for an item using the configured convention."""
    from pydatalab.config import CONFIG
    from pydatalab.mongo import get_database

    refcode = f"{CONFIG.REFCODE_GENERATOR.generate()}"
    try:
        while get_database().items.find_one({"refcode": refcode}):
            refcode = f"{CONFIG.IDENTIFIER_PREFIX}:{CONFIG.REFCODE_GENERATOR.generate()}"
    except Exception as exc:
        raise RuntimeError(f"Cannot check refcode for uniqueness: {exc}")

    return refcode


class InlineSubstance(BaseModel):
    name: str
    chemform: str | None


class EntryReference(BaseModel):
    """A reference to a database entry by ID and type.

    Can include additional arbitarary metadata useful for
    inlining the item data.

    """

    type: str
    name: str | None
    immutable_id: PyObjectId | None
    item_id: HumanReadableIdentifier | None
    refcode: Refcode | None

    @root_validator
    def check_id_fields(cls, values):
        """Check that at least one of the possible identifier fields is provided."""
        id_fields = ("immutable_id", "item_id", "refcode")

        if all(values.get(f) is None for f in id_fields):
            raise ValueError(f"Must provide at least one of {id_fields!r}")

        return values

    class Config:
        extra = "allow"


class Constituent(BaseModel):
    """A constituent of a sample."""

    item: EntryReference | InlineSubstance
    """A reference to item (sample or starting material) entry for the constituent substance."""

    quantity: float | None = Field(..., ge=0)
    """The amount of the constituent material used to create the sample."""

    unit: str = Field("g")
    """The unit symbol for the value provided in `quantity`, default is mass
    in grams (g) but could also refer to volumes (mL, L, etc.) or moles (mol).
    """

    @validator("item")
    def check_itemhood(cls, v):
        """Check that the reference within the constituent is to an item type."""
        if "type" in (v.value for v in ItemType):
            raise ValueError(f"`type` must be one of {ItemType!r}")

        return v

    @validator("item", pre=True, always=True)
    def coerce_reference(cls, v):
        if isinstance(v, dict):
            refcode = v.pop("refcode", None)
            item_id = v.pop("item_id", None)

            if refcode:
                return EntryReference(refcode=refcode, item_id=item_id, **v)
            elif item_id:
                return EntryReference(item_id=item_id, **v)
            else:
                name = v.pop("name", "")
                chemform = v.pop("chemform", None)
                if not name:
                    raise ValueError("Inline substance must have a name!")
                return InlineSubstance(name=name, chemform=chemform)
        return v
