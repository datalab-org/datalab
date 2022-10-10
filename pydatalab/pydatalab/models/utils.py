import datetime

import pint
from bson.objectid import ObjectId
from typing_extensions import TypeAlias


class PintType(str):
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
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


def datetime_from_isoformat_or_datetime(value):
    try:
        value = datetime.datetime.fromisoformat(value)
    except TypeError:
        return value


JSON_ENCODERS = {pint.Quantity: str, datetime.datetime: datetime_from_isoformat_or_datetime}
