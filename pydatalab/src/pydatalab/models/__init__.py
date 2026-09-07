import functools
import inspect

from pydatalab.models.blocks import Block
from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.items import Item
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial
from pydatalab.models.versions import BlockVersion, ItemVersion


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


# Snapshot of the built-in item types, used to reject custom registrations that
# collide with a reserved type. Populated by the bootstrapping call to
# `refresh_item_models` below, which is the only call made before it is set.
BUILTIN_ITEM_TYPES: frozenset[str] = frozenset()


def refresh_item_models() -> None:
    """Rebuild the built-in entries of `ITEM_MODELS`/`ITEM_SCHEMAS` in place from
    the current set of `Item` subclasses.

    Custom item types are deliberately *not* rediscovered by the subclass walk:
    they are owned by `register_item_model`, which validates them and rewrites
    un-namespaced types in place. Picking them up here would register whatever
    `type` they happen to declare, bypassing that namespacing, so any already
    registered custom types are left untouched instead.
    """
    get_item_models.cache_clear()
    generate_schemas.cache_clear()

    models = get_item_models()
    schemas = generate_schemas()

    if BUILTIN_ITEM_TYPES:
        models = {t: model for t, model in models.items() if t in BUILTIN_ITEM_TYPES}
        schemas = {t: schema for t, schema in schemas.items() if t in BUILTIN_ITEM_TYPES}
    else:
        # Bootstrapping call at import time: only the built-ins exist.
        ITEM_MODELS.clear()
        ITEM_SCHEMAS.clear()

    ITEM_MODELS.update(models)
    ITEM_SCHEMAS.update(schemas)


refresh_item_models()

BUILTIN_ITEM_TYPES = frozenset(ITEM_MODELS)


def _namespace_item_model(model: type[Item], item_type: str) -> str:
    """Rewrite the `type` literal of an item model *in place* to `item_type`.

    Custom item types are namespaced with a leading to
    reserve the un-prefixed namespace for built-in types. Rather than
    registering a synthesised subclass carrying the namespaced literal, the
    declaring class itself is modified, so that a model constructed directly by
    plugin code (`MySample(item_id=...)`) and one constructed by the server
    through the registry agree on their `type`, and so that `isinstance` checks
    against the declaring class continue to hold.

    Returns the namespaced type.
    """
    from typing import Literal

    from pydantic.fields import FieldInfo

    # Imported lazily: `pydatalab.logger` pulls in `CONFIG`, which imports this
    # module, so a top-level import would be circular.
    from pydatalab.logger import LOGGER

    field = model.model_fields["type"]
    fields = getattr(model, "__pydantic_fields__", model.model_fields)
    fields["type"] = FieldInfo(
        annotation=Literal[item_type],  # type: ignore[valid-type]
        default=item_type,
        description=field.description,
    )
    # Force a rebuild so the validators and (JSON) schemas are regenerated from
    # the rewritten field rather than the cached core schema.
    model.model_rebuild(force=True)

    LOGGER.debug("Namespaced custom item type of %s as %s", model.__name__, item_type)

    return item_type


def register_item_model(model: type[Item]) -> None:
    """Register a custom `Item` subclass into the global registries in place.

    Validates that `model` is a concrete `Item` subclass declaring its own
    unique `type` literal that does not collide with a built-in type. A type
    that is not already namespaced (i.e. does not begin with an underscore) is
    rewritten in place by `_namespace_item_model`, so a model declaring
    `my_samples` is registered and served as `_my_samples`. Safe to call
    repeatedly with the same model.
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

    if not item_type.startswith("_"):
        item_type = _namespace_item_model(model, f"_{item_type}")

    existing = ITEM_MODELS.get(item_type)
    if existing is not None and existing is not model:
        raise ValueError(
            f"Item type {item_type!r} is already registered to {existing.__name__!r}; "
            f"cannot register {model.__name__!r}."
        )

    ITEM_MODELS[item_type] = model
    ITEM_SCHEMAS[item_type] = model.model_json_schema(by_alias=False)


def constituent_item_types() -> set[str]:
    """Return the set of registered item types that may be referenced as a
    constituent of another item (e.g. in `synthesis_constituents`).

    An item can be a constituent if its model carries substance information
    (i.e. mixes in `HasSubstanceInfo`), which is true of the built-in `samples`
    and `starting_materials` types and of any custom item type that opts in.
    This is computed from the live registry on each call, so custom item types
    registered at startup are included.
    """
    from pydatalab.models.traits import HasSubstanceInfo

    return {
        item_type for item_type, model in ITEM_MODELS.items() if issubclass(model, HasSubstanceInfo)
    }


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
    "Block",
    "BlockVersion",
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
    "constituent_item_types",
)
