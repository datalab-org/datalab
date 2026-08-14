import functools
import inspect

from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.items import Item
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.schema_hints import validate_schema_hints
from pydatalab.models.starting_materials import StartingMaterial
from pydatalab.models.versions import ItemVersion


def _item_type_for(model: type[Item]) -> str:
    """Return the `type` literal default declared by an item model."""
    return model.model_json_schema()["properties"]["type"]["default"]


def _all_item_subclasses(base: type[Item] = Item) -> list[type[Item]]:
    """Recursively collect all concrete (non-abstract) subclasses of `Item`.

    Unlike `Item.__subclasses__()`, this walks the full subclass tree so that
    custom item types defined as subclasses of a *concrete* built-in (e.g.
    `class MySample(Sample)`) are also discovered. Base classes appear before
    their own subclasses, so callers can resolve `type` collisions in favour of
    the more general (built-in) class via first-seen-wins.
    """
    subclasses: list[type[Item]] = []
    for subclass in base.__subclasses__():
        if not inspect.isabstract(subclass):
            subclasses.append(subclass)
        subclasses.extend(_all_item_subclasses(subclass))
    return subclasses


@functools.lru_cache(maxsize=1)
def get_item_models() -> dict[str, type[Item]]:
    """Returns a dictionary of item models keyed by their type.

    If two models declare the same `type`, the first one seen wins (built-ins
    are defined first, so they are never clobbered by a custom subclass that
    forgot to override its `type` literal).
    """
    models: dict[str, type[Item]] = {}
    for model in _all_item_subclasses():
        models.setdefault(_item_type_for(model), model)
    return models


@functools.lru_cache(maxsize=1)
def generate_schemas() -> dict[str, dict]:
    return {t: model.model_json_schema(by_alias=False) for t, model in get_item_models().items()}


# The registries are populated in place by `refresh_item_models` below and are
# imported *by value* across the codebase (e.g. `from pydatalab.models import
# ITEM_MODELS`). They must therefore always be mutated in place, never
# reassigned, so that those importers observe later (dynamic) registrations.
ITEM_MODELS: dict[str, type[Item]] = {}
ITEM_SCHEMAS: dict[str, dict] = {}


def refresh_item_models() -> None:
    """Rebuild `ITEM_MODELS`/`ITEM_SCHEMAS` in place from the current set of
    `Item` subclasses, picking up any models imported since the last build."""
    get_item_models.cache_clear()
    generate_schemas.cache_clear()
    ITEM_MODELS.clear()
    ITEM_MODELS.update(get_item_models())
    ITEM_SCHEMAS.clear()
    ITEM_SCHEMAS.update(generate_schemas())


refresh_item_models()

# Snapshot of the built-in item types, used to reject custom registrations that
# collide with a reserved type.
BUILTIN_ITEM_TYPES: frozenset[str] = frozenset(ITEM_MODELS)


def register_item_model(model: type[Item]) -> None:
    """Register a custom `Item` subclass into the global registries in place.

    Validates that `model` is a concrete `Item` subclass declaring its own
    unique `type` literal that does not collide with a built-in type. Safe to
    call repeatedly with the same model.
    """
    if not (isinstance(model, type) and issubclass(model, Item)):
        raise TypeError(f"{model!r} must be a subclass of Item to be registered as an item type.")

    if inspect.isabstract(model):
        raise TypeError(f"Cannot register abstract item model {model!r}.")

    item_type = _item_type_for(model)

    if item_type in BUILTIN_ITEM_TYPES:
        raise ValueError(
            f"Custom item model {model.__name__!r} uses the reserved built-in type {item_type!r}; "
            "custom types must declare their own unique `type` literal."
        )

    existing = ITEM_MODELS.get(item_type)
    if existing is not None and existing is not model:
        raise ValueError(
            f"Item type {item_type!r} is already registered to {existing.__name__!r}; "
            f"cannot register {model.__name__!r}."
        )

    validate_schema_hints(model)

    ITEM_MODELS[item_type] = model
    ITEM_SCHEMAS[item_type] = model.model_json_schema(by_alias=False)


def flagged_summary_fields(types) -> list[str]:
    """Return the field names flagged with ``datalab_include_field_in_summary``
    in the schemas of the given item types.

    Used by the item list/summary endpoints to project additional fields beyond
    the hand-tuned base projection, so that (custom or built-in) fields opt into
    list views declaratively, e.g.::

        drying_time: float | None = Field(
            None, json_schema_extra={"datalab_include_field_in_summary": True}
        )
    """
    fields: set[str] = set()
    for item_type in types:
        schema = ITEM_SCHEMAS.get(item_type)
        if not schema:
            continue
        for name, prop in schema.get("properties", {}).items():
            if isinstance(prop, dict) and prop.get("datalab_include_field_in_summary"):
                fields.add(name)
    return sorted(fields)


def load_custom_item_models(paths: list[str]) -> None:
    """Import and register custom item models from a list of dotted paths.

    Each path is of the form ``"package.module:ClassName"`` and must resolve to
    a concrete `Item` subclass declaring its own unique `type` literal. Used to
    dynamically register deployment-specific item types from the config without
    packaging them as plugins.
    """
    import importlib

    for path in paths:
        module_path, _, attr = path.partition(":")
        if not module_path or not attr:
            raise ValueError(
                f"Invalid custom item model path {path!r}; expected 'package.module:ClassName'."
            )
        module = importlib.import_module(module_path)
        register_item_model(getattr(module, attr))


__all__ = (
    "File",
    "Sample",
    "StartingMaterial",
    "Person",
    "Cell",
    "Collection",
    "Equipment",
    "ItemVersion",
    "ITEM_MODELS",
    "ITEM_SCHEMAS",
    "BUILTIN_ITEM_TYPES",
    "register_item_model",
    "refresh_item_models",
    "load_custom_item_models",
    "flagged_summary_fields",
)
