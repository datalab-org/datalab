"""Translation of OPTIMADE filter strings into MongoDB queries for advanced search.

The advanced-search ``/query`` route accepts a ``filter`` written in the
[OPTIMADE filter language](https://www.optimade.org/specification/latest/#api-filtering-format-specification).
Parsing is done with the reference grammar from ``optimade-python-tools``; this
module only adapts its MongoDB transformer to datalab's field registry (property
names, timestamp fields and regex escaping).
"""

import re
from datetime import datetime, timezone
from typing import Any

from lark import v_args
from lark.exceptions import VisitError
from optimade.exceptions import BadRequest
from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer, recursive_postprocessing

OPTIMADE_FILTER_VERSION = (1, 2, 0)
MAX_FILTER_LENGTH = 10_000

_PARSER = LarkParser(version=OPTIMADE_FILTER_VERSION)
_STRING_ESCAPE = re.compile(r'\\(["\\])')


class InvalidFilter(ValueError):
    """Raised when a filter cannot be parsed or refers to unsupported properties."""


class _FieldPath(str):
    """A MongoDB path produced from an OPTIMADE property, so that it can be told apart
    from a string literal on the right-hand side of a comparison."""


def parse_rfc3339(value: str) -> datetime:
    """Parse an OPTIMADE timestamp (RFC 3339, e.g. ``2026-01-31T12:00:00Z``) as UTC."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidFilter(
            f'{value!r} is not a valid timestamp, expected e.g. "2026-01-31T12:00:00Z"'
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class DatalabMongoTransformer(MongoTransformer):
    """OPTIMADE → MongoDB transformer restricted to the fields of one advanced-search view.

    ``field_registry`` maps OPTIMADE property names (as listed by ``/query/<type>/schema``) to
    their registry entries, which provide the ``mongo_path`` and ``value_type``.
    """

    def __init__(self, field_registry: dict[str, dict]):
        super().__init__(mapper=None)
        self.field_registry = field_registry
        self.timestamp_paths = {
            f["mongo_path"] for f in field_registry.values() if f.get("value_type") == "timestamp"
        }

    def property(self, args):
        name = ".".join(str(arg) for arg in args)
        field = self.field_registry.get(name)
        if field:
            return _FieldPath(field["mongo_path"])
        if name.startswith("_"):
            # Provider-specific properties that this database does not serve MUST be
            # treated as unknown rather than raising an error.
            return _FieldPath(f"_optimade_unknown.{name}")
        raise BadRequest(detail=f"'{name}' is not a known or searchable property")

    def string(self, args):
        # string: ESCAPED_STRING, where only \" and \\ are valid escapes.
        return _STRING_ESCAPE.sub(r"\1", str(args[0])[1:-1])

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        if isinstance(value, _FieldPath):
            raise BadRequest(detail="Comparisons between two properties are not supported")
        return super().value_op_rhs(operator, value)

    def fuzzy_string_op_rhs(self, arg):
        # fuzzy_string_op_rhs: CONTAINS value | STARTS [ WITH ] value | ENDS [ WITH ] value
        pattern = arg[-1]
        if not isinstance(pattern, str) or isinstance(pattern, _FieldPath):
            raise BadRequest(detail=f"{arg[0]} requires a string value")
        escaped = re.escape(pattern)
        if arg[0] == "STARTS":
            return {"$regex": f"^{escaped}"}
        if arg[0] == "ENDS":
            return {"$regex": f"{escaped}$"}
        return {"$regex": escaped}

    def _apply_mongo_date_filter(self, filter_: dict) -> dict:
        def is_timestamp_comparison(prop, expr):
            return prop in self.timestamp_paths and isinstance(expr, dict)

        def convert(subdict, prop, expr):
            subdict[prop] = {
                op: parse_rfc3339(val) if isinstance(val, str) else val for op, val in expr.items()
            }
            return subdict

        return recursive_postprocessing(filter_, is_timestamp_comparison, convert)


def compile_filter(filter_: str | None, field_registry: dict[str, dict]) -> dict[str, Any]:
    """Compile an OPTIMADE filter string into a MongoDB query (``{}`` for an empty filter)."""
    if filter_ is None or not str(filter_).strip():
        return {}
    if not isinstance(filter_, str):
        raise InvalidFilter("filter must be a string")
    if len(filter_) > MAX_FILTER_LENGTH:
        raise InvalidFilter(f"filter is longer than {MAX_FILTER_LENGTH} characters")

    try:
        tree = _PARSER.parse(filter_)
        query = DatalabMongoTransformer(field_registry).transform(tree) or {}
    except VisitError as exc:
        raise _as_invalid_filter(exc.orig_exc) from exc
    except Exception as exc:
        raise _as_invalid_filter(exc) from exc
    _check_compares_properties(query)
    return query


def _check_compares_properties(query: Any) -> None:
    """Reject comparisons without a property, e.g. ``1 = 1``: the grammar allows them, but
    they would reach the database with a non-string field name."""
    if isinstance(query, list):
        for part in query:
            _check_compares_properties(part)
    elif isinstance(query, dict):
        for key, value in query.items():
            if not isinstance(key, str):
                raise InvalidFilter("Each comparison in the filter must involve a property")
            _check_compares_properties(value)


def _as_invalid_filter(exc: Exception) -> InvalidFilter:
    if isinstance(exc, InvalidFilter):
        return exc
    if isinstance(exc, BadRequest):
        # The parser's message embeds a full Lark traceback; keep only the summary line
        # and the pointer to the offending position.
        lines = [line for line in str(exc.detail).splitlines() if line.strip()]
        return InvalidFilter(" ".join(lines[:4]) if lines else "Invalid filter")
    if isinstance(exc, NotImplementedError):
        return InvalidFilter(f"Unsupported filter feature: {exc}")
    return InvalidFilter(f"Invalid filter: {exc}")
