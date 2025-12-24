from pydantic import BaseModel

from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial
from pydatalab.models.versions import ItemVersion

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
    "ItemVersion",
    "ITEM_MODELS",
)
