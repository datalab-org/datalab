from typing import Dict, Type

from pydantic import BaseModel

from pydatalab.models.cells import Cell
from pydatalab.models.collections import Collection
from pydatalab.models.equipment import Equipment
from pydatalab.models.files import File
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial

ITEM_MODELS: Dict[str, Type[BaseModel]] = {
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
