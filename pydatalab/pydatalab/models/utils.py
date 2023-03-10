import datetime
import random
import string
from enum import Enum
from functools import partial
from typing import Callable

import pint
from bson.objectid import ObjectId
from pydantic import ConstrainedStr, parse_obj_as
from typing_extensions import TypeAlias


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
    def validate(cls, v):
        if isinstance(v, str):
            if v in ["0", " "]:
                return None
            return datetime.datetime.fromisoformat(v)

        return v

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="date")


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
    return "".join(random.choices(string.ascii_uppercase, k=length))


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
