from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, Field


class TgaTemperatureStep(BaseModel):
    initial_temp: float
    final_temp: float
    ramp_rate: float
    hold_time: float
    sampling_time: float
    gas1_status: bool
    gas2_status: bool
    store: bool


class TgaTemperatureStepUnits(BaseModel):
    initial_temp: str
    final_temp: str
    ramp_rate: str
    hold_time: str
    sampling_time: str


class TgaTemperatureProgram(BaseModel):
    steps: List[TgaTemperatureStep]
    units: TgaTemperatureStepUnits


class TgaMetadata(BaseModel):
    module: str = Field(None, alias="Module")
    channel: str = Field(None, alias="Channel")
    data_name: str = Field(None, alias="Data Name")
    measurement_time: str = Field(None, alias="Measurement Time")
    sample_name: str = Field(None, alias="Sample Name")
    sample_weight: float = Field(None, alias="Sample Weight")
    reference_name: str = Field(None, alias="Reference Name")
    reference_weight: float = Field(None, alias="Reference Weight")
    temperature_program: TgaTemperatureProgram = Field(None, alias="temperature_program")
    temperature_program_mode: str = Field(None, alias="Temperature Program Mode")
    operator_name: str = Field(None, alias="Operator Name")
    organization_name: Optional[str] = Field(None, alias="Organization Name")
    operator: Optional[str] = Field(None, alias="Operator")
    gas1: Optional[str] = Field(None, alias="Gas1")
    gas2: Optional[str] = Field(None, alias="Gas1")
    pan: Optional[str] = Field(None, alias="Pan")


class TgaData(BaseModel):
    tabular_data: pd.DataFrame  # we should do additional typing here...

    class Config:
        arbitrary_types_allowed = True
