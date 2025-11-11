import functools

from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.items import Item
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial


@functools.lru_cache(maxsize=1)
def get_item_models() -> dict[str, type[Item]]:
    """
    Returns a dictionary of item models keyed by their type.
    """
    return {
        model.model_json_schema()["properties"]["type"]["default"]: model
        for model in Item.__subclasses__()
    }


@functools.lru_cache(maxsize=1)
def generate_schemas() -> dict[str, dict]:
    return {t: model.model_json_schema(by_alias=False) for t, model in get_item_models().items()}


ITEM_MODELS: dict[str, type[Item]] = get_item_models()
ITEM_SCHEMAS = generate_schemas()

__all__ = (
    "File",
    "Sample",
    "StartingMaterial",
    "Person",
    "Cell",
    "Collection",
    "Equipment",
    "ITEM_MODELS",
    "ITEM_SCHEMAS",
)
