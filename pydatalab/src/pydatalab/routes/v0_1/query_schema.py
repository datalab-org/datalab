"""Schema introspection for advanced search.

Builds, for each searchable datalab type, the registry of properties and OPTIMADE filter
operators that :mod:`pydatalab.routes.v0_1.query` reports to the query builder and uses to
compile filters. Kept separate from the route handlers so that "what can be queried" stays
independent of "how a query request is served".
"""

import re
from functools import lru_cache
from typing import Any

from pydatalab.models import ITEM_MODELS
from pydatalab.models.collections import Collection
from pydatalab.models.people import Group, Person

QUERY_VIEWS: dict[str, dict] = {
    "samples": {
        "resource": "items",
        "collection": "items",
        "types": ["samples", "cells"],
        "model_by_type": ITEM_MODELS,
        "view_contexts": ["samples"],
        "default_sort": [("date", -1)],
    },
    "starting_materials": {
        "resource": "items",
        "collection": "items",
        "types": ["starting_materials"],
        "model_by_type": ITEM_MODELS,
        "view_contexts": ["startingMaterials", "starting_materials"],
        "default_sort": [("date", -1)],
    },
    "equipment": {
        "resource": "items",
        "collection": "items",
        "types": ["equipment"],
        "model_by_type": ITEM_MODELS,
        "view_contexts": ["equipment"],
        "default_sort": [("date", -1)],
    },
    "collections": {
        "resource": "collections",
        "collection": "collections",
        "types": ["collections"],
        "model_by_type": {"collections": Collection},
        "view_contexts": ["collections"],
        "default_sort": [("_id", -1)],
    },
    "users": {
        "resource": "users",
        "collection": "users",
        "model": Person,
        "view_contexts": ["users"],
        # Like the /users and /groups admin routes, only admins may search these.
        "admin_only": True,
        "default_sort": [("display_name", 1)],
    },
    "groups": {
        "resource": "groups",
        "collection": "groups",
        "model": Group,
        "view_contexts": ["groups"],
        "admin_only": True,
        "default_sort": [("display_name", 1)],
    },
}

_SKIP_FIELDS: set[str] = {
    "type",
    "immutable_id",
    "creator_ids",
    "group_ids",
    "blocks_obj",
    "display_order",
    "file_ObjectIds",
    "revision",
    "revisions",
    "version",
    "relationships",
    "files",
    "collections",
    "creators",
    "groups",
    # Items only store tag references (`{type, immutable_id}`); names are resolved on read,
    # so none of the tag's fields can be matched in the database.
    "tags",
}

_FIELD_UI: dict[str, dict] = {
    "name": {"label": "Name", "group": "Basic", "sortable": True},
    "item_id": {"label": "Item ID", "group": "Basic", "sortable": True},
    "refcode": {"label": "Refcode", "group": "Basic", "sortable": True},
    "description": {"label": "Description", "group": "Basic", "sortable": False},
    "date": {"label": "Date", "group": "Basic", "sortable": True},
    "status": {"label": "Status", "group": "Basic", "sortable": True, "groupable": True},
    "chemform": {
        "label": "Formula",
        "group": "Chemistry",
        "sortable": True,
        "editor_override": {"=": "chemical-formula"},
    },
    "characteristic_chemical_formula": {
        "label": "Active material formula",
        "group": "Chemistry",
        "sortable": True,
        "editor_override": {"=": "chemical-formula"},
    },
    "smiles": {"label": "SMILES", "group": "Chemistry", "sortable": False},
    "inchi_key": {"label": "InChI key", "group": "Chemistry", "sortable": False},
    "inchi": {"label": "InChI", "group": "Chemistry", "sortable": False},
    "GHS_codes": {"label": "GHS hazard codes", "group": "Chemistry", "sortable": False},
    "CAS": {"label": "CAS number", "group": "Chemistry", "sortable": False},
    "molar_mass": {"label": "Molar mass (g/mol)", "group": "Chemistry", "sortable": True},
    "characteristic_mass": {
        "label": "Characteristic mass (mg)",
        "group": "Chemistry",
        "sortable": True,
    },
    "characteristic_molar_mass": {
        "label": "Characteristic molar mass",
        "group": "Chemistry",
        "sortable": True,
    },
    "cell_format": {"label": "Cell format", "group": "Cell", "sortable": True, "groupable": True},
    "cell_format_description": {
        "label": "Cell format description",
        "group": "Cell",
        "sortable": False,
    },
    "cell_preparation_description": {
        "label": "Cell preparation",
        "group": "Cell",
        "sortable": False,
    },
    "supplier": {"label": "Supplier", "group": "Provenance", "sortable": True, "groupable": True},
    "location": {"label": "Location", "group": "Provenance", "sortable": True, "groupable": True},
    "manufacturer": {
        "label": "Manufacturer",
        "group": "Provenance",
        "sortable": True,
        "groupable": True,
    },
    "serial_numbers": {"label": "Serial numbers", "group": "Provenance", "sortable": False},
    "contact": {"label": "Contact", "group": "Provenance", "sortable": False},
    "barcode": {"label": "Barcode", "group": "Provenance", "sortable": False},
    "chemical_purity": {"label": "Chemical purity", "group": "Chemistry", "sortable": False},
    "synthesis_description": {
        "label": "Synthesis description",
        "group": "Synthesis",
        "sortable": False,
    },
    "synthesis_constituents": {
        "label": "Synthesis constituent",
        "group": "Synthesis",
        "sortable": False,
    },
    "date_opened": {"label": "Date opened", "group": "Provenance", "sortable": True},
    "last_modified": {"label": "Last modified", "group": "Basic", "sortable": True},
    "active_ion_charge": {"label": "Active ion charge", "group": "Cell", "sortable": True},
    "positive_electrode": {
        "label": "Positive electrode constituent",
        "group": "Cell",
        "sortable": False,
    },
    "negative_electrode": {
        "label": "Negative electrode constituent",
        "group": "Cell",
        "sortable": False,
    },
    "electrolyte": {"label": "Electrolyte constituent", "group": "Cell", "sortable": False},
}


# Operators of the OPTIMADE filter language, keyed by their literal token(s), see
# https://www.optimade.org/specification/latest/#api-filtering-format-specification
# Only UI metadata lives here: the filter string itself is parsed and compiled to a
# mongo query by :mod:`pydatalab.routes.v0_1.query_filter`.
OPERATORS: dict[str, dict] = {
    "=": {"label": "=", "value_required": True},
    "!=": {"label": "!=", "value_required": True},
    "<": {"label": "<", "value_required": True},
    "<=": {"label": "<=", "value_required": True},
    ">": {"label": ">", "value_required": True},
    ">=": {"label": ">=", "value_required": True},
    "CONTAINS": {"label": "CONTAINS", "value_required": True, "editor": "text"},
    "STARTS WITH": {"label": "STARTS WITH", "value_required": True, "editor": "text"},
    "ENDS WITH": {"label": "ENDS WITH", "value_required": True, "editor": "text"},
    "HAS": {"label": "HAS", "value_required": True},
    "HAS ALL": {"label": "HAS ALL", "value_required": True, "editor": "string-list"},
    "HAS ANY": {"label": "HAS ANY", "value_required": True, "editor": "string-list"},
    "HAS ONLY": {"label": "HAS ONLY", "value_required": True, "editor": "string-list"},
    "LENGTH": {"label": "LENGTH", "value_required": True, "editor": "number"},
    "IS KNOWN": {"label": "IS KNOWN", "value_required": False},
    "IS UNKNOWN": {"label": "IS UNKNOWN", "value_required": False},
}

# Editor used for an operator's value when the operator does not fix one itself.
VALUE_TYPE_EDITORS: dict[str, str] = {
    "string": "text",
    "number": "number",
    "timestamp": "datetime",
    "enum": "enum",
}

_KNOWN_OPS = ["IS KNOWN", "IS UNKNOWN"]
_OPERATORS_BY_KIND: dict[str, list[str]] = {
    "string": ["=", "!=", "CONTAINS", "STARTS WITH", "ENDS WITH", *_KNOWN_OPS],
    "number": ["=", "!=", "<", "<=", ">", ">=", *_KNOWN_OPS],
    "timestamp": [">=", "<=", ">", "<", "=", "!=", *_KNOWN_OPS],
    "enum": ["=", "!=", *_KNOWN_OPS],
    # A list property, e.g. `tags`.
    "list": ["HAS", "HAS ALL", "HAS ANY", "HAS ONLY", "LENGTH", *_KNOWN_OPS],
    # A property reached through a list of dictionaries, e.g. `synthesis_constituents.item.name`:
    # it holds one value per list entry, so only the set operators that do not depend on
    # the list as a whole are meaningful.
    "nested_list": ["HAS", "HAS ANY", "HAS ALL", *_KNOWN_OPS],
}

# OPTIMADE property names: lowercase identifiers, optionally nested with dots.
_OPTIMADE_PROPERTY = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")


def optimade_property_name(path: str) -> str | None:
    """Return the OPTIMADE property name for a model field path, or None if it has none."""
    name = path.lower()
    return name if _OPTIMADE_PROPERTY.match(name) else None


def _model_schema(model: Any) -> dict:
    return model.model_json_schema(by_alias=False)


def _resolve_ref(ref: str, definitions: dict) -> dict:
    name = ref.split("/")[-1]
    return definitions.get(name, {})


def _unwrap_nullable(field_def: dict) -> dict:
    """Collapse pydantic v2's ``Optional[X]`` form (``anyOf: [X, {"type": "null"}]``) into X."""
    branches = [b for b in field_def.get("anyOf", []) if b.get("type") != "null"]
    if len(branches) != 1 or len(branches) == len(field_def["anyOf"]):
        return field_def
    unwrapped = {k: v for k, v in field_def.items() if k != "anyOf"}
    unwrapped.update(branches[0])
    return unwrapped


def _resolve_schema_node(field_def: dict, definitions: dict) -> dict:
    for candidate in (field_def, *field_def.get("allOf", []), *field_def.get("anyOf", [])):
        ref = candidate.get("$ref", "")
        if ref:
            return _resolve_ref(ref, definitions)
    return field_def


def _field_to_operators(
    field_def: dict, definitions: dict, field_name: str, via_array: bool = False
) -> dict | None:
    """Describe how a model field can be queried, or return None if it cannot be.

    Returns a dict with the field's scalar ``value_type`` (string, number, timestamp or
    enum), whether it ``is_list``, its OPTIMADE ``operator_ids`` and any per-operator
    ``editor_override``/``value_schema_override`` for the frontend.
    """
    node = _resolve_schema_node(_unwrap_nullable(field_def), definitions)
    is_list = node.get("type") == "array"
    if is_list:
        node = _resolve_schema_node(_unwrap_nullable(node.get("items") or {}), definitions)

    fmt = node.get("format", "")
    ftype = node.get("type", "")
    leaf_name = field_name.split(".")[-1]
    value_schema: dict = {}

    if node.get("enum"):
        value_type = "enum"
        value_schema = {"enum": node["enum"]}
    elif fmt == "date-time" or (
        ftype == "string" and ("date" in leaf_name or leaf_name == "last_modified")
    ):
        value_type = "timestamp"
    elif ftype in ("number", "integer"):
        value_type = "number"
    elif ftype == "string":
        value_type = "string"
    else:
        return None

    if is_list:
        kind = "list"
    elif via_array:
        kind = "nested_list"
    else:
        kind = value_type
    operator_ids = list(_OPERATORS_BY_KIND[kind])

    editor_override = dict(_FIELD_UI.get(field_name, {}).get("editor_override", {}))
    value_schema_override: dict = {}
    if value_type == "enum":
        for op_id in ("=", "!=", "HAS"):
            if op_id in operator_ids:
                editor_override.setdefault(op_id, "enum")
                value_schema_override[op_id] = value_schema

    return {
        "value_type": value_type,
        "is_list": is_list or via_array,
        "operator_ids": operator_ids,
        "editor_override": editor_override,
        "value_schema_override": value_schema_override,
    }


def _iter_schema_fields(
    properties: dict, definitions: dict, prefix: str = "", depth: int = 0, via_array: bool = False
) -> list[tuple[str, dict, bool]]:
    """Flatten a JSON schema into ``(dotted path, field schema, reached through a list)``."""
    fields: list[tuple[str, dict, bool]] = []
    for field_name, field_def in properties.items():
        path = f"{prefix}.{field_name}" if prefix else field_name
        if not prefix and field_name in _SKIP_FIELDS:
            continue
        # Stored as ObjectIds, which a filter's string values can never equal.
        if field_name == "immutable_id":
            continue

        field_def = _unwrap_nullable(field_def)

        resolved = _resolve_schema_node(field_def, definitions)
        node = resolved or field_def
        nested_properties = node.get("properties")
        array_items = node.get("items", {})
        array_node = _resolve_schema_node(array_items, definitions) if array_items else {}

        if node.get("type") == "array" and array_node.get("properties") and depth < 3:
            fields.extend(
                _iter_schema_fields(array_node["properties"], definitions, path, depth + 1, True)
            )
            continue

        if nested_properties and depth < 3:
            fields.extend(
                _iter_schema_fields(nested_properties, definitions, path, depth + 1, via_array)
            )
            continue

        fields.append((path, field_def, via_array))

    return fields


def _build_model_field_registry(model: Any, type_id: str) -> dict[str, dict]:
    try:
        schema = _model_schema(model)
        definitions = schema.get("$defs", {})
        properties = schema.get("properties", {})
    except Exception:
        definitions = {}
        properties = {}

    registry: dict[str, dict] = {}
    for field_name, field_def, via_array in _iter_schema_fields(properties, definitions):
        property_name = optimade_property_name(field_name)
        query_info = _field_to_operators(field_def, definitions, field_name, via_array)
        if not property_name or not query_info or property_name in registry:
            continue

        ui = _FIELD_UI.get(field_name, {})
        label = ui.get("label") or field_name.replace("_", " ").title()
        group = ui.get("group", "Other")
        sortable = ui.get(
            "sortable",
            not query_info["is_list"] and query_info["value_type"] in ("string", "number"),
        )
        groupable = ui.get("groupable", False)

        registry[property_name] = {
            "mongo_path": field_name,
            "label": label,
            "group": group,
            "sortable": sortable,
            "groupable": groupable,
            **query_info,
        }

    # Constituents are lists of item references: query them by the referenced item ID,
    # with a picker for the item rather than a free-text value.
    _constituent_fields = {
        "synthesis_constituents": ("Synthesis constituent", "Synthesis"),
        "positive_electrode": ("Positive electrode constituent", "Cell"),
        "negative_electrode": ("Negative electrode constituent", "Cell"),
        "electrolyte": ("Electrolyte constituent", "Cell"),
    }
    for cf_name, (cf_label, cf_group) in _constituent_fields.items():
        if cf_name in properties:
            registry[f"{cf_name}.item.item_id"] = {
                "mongo_path": f"{cf_name}.item.item_id",
                "label": cf_label,
                "group": cf_group,
                "sortable": False,
                "groupable": False,
                "value_type": "string",
                "is_list": True,
                "operator_ids": list(_OPERATORS_BY_KIND["nested_list"]),
                "editor_override": {"HAS": "constituent-selector"},
                "value_schema_override": {},
            }

    return registry


def _get_field_registry(
    selected_types: list[str], model_by_type: dict | None = None
) -> dict[str, dict]:
    models = model_by_type or ITEM_MODELS
    registries = [_build_model_field_registry(models[t], t) for t in selected_types]
    common_ids = set(registries[0].keys())
    for r in registries[1:]:
        common_ids &= set(r.keys())
    return {fid: registries[0][fid] for fid in common_ids}


def _build_field_registry_for_view(
    list_view: str, view: dict, selected_types: list[str] | None = None
) -> dict[str, dict]:
    if view.get("model"):
        # single-model view
        return _build_model_field_registry(view["model"], list_view)

    model_by_type = view.get("model_by_type") or ITEM_MODELS
    types = selected_types or view.get("types") or list(model_by_type.keys())
    return _get_field_registry(types, model_by_type)


def _model_label(model: Any | None, fallback: str) -> str:
    if not model:
        return fallback
    try:
        return _model_schema(model).get("title", fallback)
    except Exception:
        return fallback


def _build_searchable_types() -> dict[str, dict]:
    types: dict[str, dict] = {}
    for list_view, view in QUERY_VIEWS.items():
        if view.get("model_by_type"):
            models = {t: view["model_by_type"][t] for t in view.get("types", [])}
        elif view.get("model"):
            models = {list_view: view["model"]}
        else:
            continue
        for type_id, model in models.items():
            types[type_id] = {"list_view": list_view, "model": model, "view": view}
    return types


# Every datalab type advanced search can query (samples, cells, collections, ...).
SEARCHABLE_TYPES: dict[str, dict] = _build_searchable_types()


@lru_cache(maxsize=None)
def type_field_registry(type_id: str) -> dict[str, dict]:
    """The queryable properties of a type, keyed by their name in OPTIMADE filters."""
    entry = SEARCHABLE_TYPES[type_id]
    return _build_field_registry_for_view(entry["list_view"], entry["view"], [type_id])


def type_label(type_id: str) -> str:
    return _model_label(SEARCHABLE_TYPES[type_id]["model"], type_id.replace("_", " ").title())


def types_for_table(table: str | None, is_admin: bool = False) -> list[dict]:
    """The types the advanced search of a webapp table (its ``dataType``) can query; types of
    admin-only views are only listed for admins."""
    return [
        {"id": type_id, "label": type_label(type_id)}
        for type_id, entry in SEARCHABLE_TYPES.items()
        if table in entry["view"].get("view_contexts", [])
        and (is_admin or not entry["view"].get("admin_only"))
        and type_field_registry(type_id)
    ]
