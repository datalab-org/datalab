from pydantic import BaseModel

from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial

ITEM_MODELS: dict[str, type[BaseModel]] = {
    "samples": Sample,
    "starting_materials": StartingMaterial,
    "cells": Cell,
    "equipment": Equipment,
}

__all__ = (
    "File",
    "Sample",
    "StartingMaterial",
    "Person",
    "Cell",
    "Collection",
    "Equipment",
    "ITEM_MODELS",
)

MODELS_WITH_CIRCULAR_REFS: list[type[BaseModel]] = [
    *ITEM_MODELS.values(),
    Collection,
]

for model in MODELS_WITH_CIRCULAR_REFS:
    try:
        model.model_rebuild()
    except Exception as e:
        print(f"Warning: Failed to rebuild {model.__name__}: {e}")
