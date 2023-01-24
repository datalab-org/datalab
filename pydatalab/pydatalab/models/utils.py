import datetime

import pint
from bson.objectid import ObjectId
from pydantic import ConstrainedStr, parse_obj_as
from typing_extensions import TypeAlias


class HumanReadableIdentifier(ConstrainedStr):
    """Used to constrain human-readable and URL-safe identifiers for items."""

    min_length = 1
    max_length = 32
    strip_whitespace = True
    to_lower = False
    strict = False

    regex = r"^[a-zA-Z0-9_-]+$"
    """A regex to match strings without characters that need URL encoding"""

    def __init__(self, value):
        self.value = parse_obj_as(type(self), value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    def __bool__(self):
        return bool(self.value)


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
