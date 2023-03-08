from typing import Dict, Type

from pydantic import BaseModel

from pydatalab.models.cells import Cell
from pydatalab.models.files import File
from pydatalab.models.people import Person
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial

ITEM_MODELS: Dict[str, Type[BaseModel]] = {
    "samples": Sample,
    "starting_materials": StartingMaterial,
    "cells": Cell,
}

__all__ = ("File", "Sample", "StartingMaterial", "Person", "ITEM_MODELS")
