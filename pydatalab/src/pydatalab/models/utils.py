import datetime
import random
import string
from collections.abc import Callable
from enum import Enum
from functools import partial
from typing import Any, TypeAlias

import pint
from bson.objectid import ObjectId
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic_core import core_schema


class ItemType(str, Enum):
    """An enumeration of the types of items known by this implementation, should be made dynamic in the future."""

    SAMPLES = "samples"
    STARTING_MATERIALS = "starting_materials"


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


class HumanReadableIdentifier(str):
    """Used to constrain human-readable and URL-safe identifiers for items."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        import re

        from pydantic_core import core_schema

        def validate_identifier(v):
            if not isinstance(v, str):
                v = str(v)
            v = v.strip()
            if len(v) < 1 or len(v) > 40:
                raise ValueError("String must be between 1 and 40 characters")
            if not re.match(IDENTIFIER_REGEX, v):
                raise ValueError(f"String does not match required pattern: {IDENTIFIER_REGEX}")
            return cls(v)

        return core_schema.no_info_after_validator_function(
            validate_identifier,
            core_schema.union_schema([core_schema.str_schema(), core_schema.int_schema()]),
        )


class Refcode(str):
    """A regex to match refcodes that have a lower-case prefix between 2-10 chars, followed by a colon, and then the normal rules for an ID (url-safe etc.)."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        import re

        from pydantic_core import core_schema

        refcode_pattern = r"^[a-z]{2,10}:" + IDENTIFIER_REGEX[1:]

        def validate_refcode(v):
            if v is None:
                return None
            if not isinstance(v, str):
                v = str(v)
            v = v.strip()
            if len(v) < 1 or len(v) > 40:
                raise ValueError("String must be between 1 and 40 characters")
            if not re.match(refcode_pattern, v):
                raise ValueError(f"String does not match required pattern: {refcode_pattern}")
            return cls(v)

        return core_schema.no_info_after_validator_function(
            validate_refcode,
            core_schema.union_schema(
                [core_schema.str_schema(), core_schema.int_schema(), core_schema.none_schema()]
            ),
        )


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
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(str, when_used="json"),
        )

    @classmethod
    def validate(self, v):
        q = self.Q(v)
        if not q.check(self._dimensions):
            raise ValueError("Value {v} must have dimensions of mass, not {v.dimensions}")
        return q


Mass: TypeAlias = PintType("[mass]")  # type: ignore # noqa
Volume: TypeAlias = PintType("[volume]")  # type: ignore # noqa


class PyObjectId(ObjectId):
    """A wrapper class for a BSON ObjectId that can be used as a Pydantic field type.

    Modified from "Getting started iwth MongoDB and FastAPI":
    https://www.mongodb.com/developer/languages/python/python-quickstart-fastapi/.

    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.union_schema(
                [
                    core_schema.str_schema(),
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.is_instance_schema(cls),
                    core_schema.none_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x) if x else None, when_used="json"
            ),
        )

    @classmethod
    def validate(cls, v):
        if v is None:
            return None
        if isinstance(v, cls):
            return v
        if isinstance(v, ObjectId):
            return cls(ObjectId(v))
        if isinstance(v, dict) and "$oid" in v:
            v = v["$oid"]
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return cls(ObjectId(v))
        raise ValueError("Invalid ObjectId")


class IsoformatDateTime(datetime.datetime):
    """A datetime container that is more flexible than the pydantic default."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.union_schema(
                [
                    core_schema.str_schema(),
                    core_schema.is_instance_schema(datetime.datetime),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: x.isoformat() if x else None, when_used="json"
            ),
        )

    @classmethod
    def validate(cls, v) -> datetime.datetime | None:
        """Cast isoformat strings to datetimes and enforce UTC if tzinfo is missing."""
        if v is None:
            return None

        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=datetime.timezone.utc)
            return v

        if isinstance(v, str):
            if v in ["0", " ", ""]:
                return None
            v = datetime.datetime.fromisoformat(v)
            if v.tzinfo is None:
                v = v.replace(tzinfo=datetime.timezone.utc)
            return v

        raise ValueError(f"Invalid datetime value: {v}")


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
    chemform: str | None = None


class EntryReference(BaseModel):
    """A reference to a database entry by ID and type.

    Can include additional arbitarary metadata useful for
    inlining the item data.

    """

    type: str
    name: str | None = None
    immutable_id: PyObjectId | None = None
    item_id: HumanReadableIdentifier | None = None
    refcode: Refcode | None = None

    @model_validator(mode="before")
    @classmethod
    def check_id_fields(cls, values):
        """Check that at least one of the possible identifier fields is provided."""
        if not isinstance(values, dict):
            return values

        id_fields = ("immutable_id", "item_id", "refcode")

        if all(values.get(f) is None for f in id_fields):
            raise ValueError(f"Must provide at least one of {id_fields!r}")

        return values

    model_config = ConfigDict(extra="allow")


class Constituent(BaseModel):
    """A constituent of a sample."""

    item: EntryReference | InlineSubstance
    """A reference to item (sample or starting material) entry for the constituent substance."""

    quantity: float | None = Field(default=None, ge=0)
    """The amount of the constituent material used to create the sample."""

    unit: str = Field("g")
    """The unit symbol for the value provided in `quantity`, default is mass
    in grams (g) but could also refer to volumes (mL, L, etc.) or moles (mol).
    """

    @field_validator("item")
    @classmethod
    def check_itemhood(cls, v):
        """Check that the reference within the constituent is to an item type."""
        if hasattr(v, "type") and v.type not in [item_type.value for item_type in ItemType]:
            raise ValueError(f"`type` must be one of {[t.value for t in ItemType]!r}")
        return v

    @field_validator("item", mode="before")
    @classmethod
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
        elif hasattr(v, "model_dump"):
            item_id = getattr(v, "item_id", None)
            refcode = getattr(v, "refcode", None)
            item_type = getattr(v, "type", None)
            name = getattr(v, "name", None)
            chemform = getattr(v, "chemform", None)

            if item_id or refcode:
                return EntryReference(
                    item_id=item_id, refcode=refcode, type=item_type, name=name, chemform=chemform
                )
            else:
                return InlineSubstance(name=name or str(v), chemform=chemform)

        return v
