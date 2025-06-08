from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.people import Person
from pydatalab.models.items import Item
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial

ITEM_MODELS: dict[str, type[Item]] = {
    model.__fields__["type"].default: model for model in (Sample, StartingMaterial, Cell, Equipment)
}

__all__ = (
    "File",
    "Sample",
    "StartingMaterial",
    "Person",
    "Cell",
    "Item",
    "Collection",
    "Equipment",
    "ITEM_MODELS",
)
