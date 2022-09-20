from typing import Dict

from pydantic import BaseModel

from pydatalab.models.files import File
from pydatalab.models.samples import Sample
from pydatalab.models.starting_materials import StartingMaterial

ITEM_MODELS: Dict[str, BaseModel] = {"samples": Sample, "starting_materials": StartingMaterial}

__all__ = ("File", "Sample", "StartingMaterial", "ITEM_MODELS")
