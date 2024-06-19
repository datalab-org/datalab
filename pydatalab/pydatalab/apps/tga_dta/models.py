from typing import List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field, validator


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
    gas2: Optional[str] = Field(None, alias="Gas2")
    pan: Optional[str] = Field(None, alias="Pan")


class TgaData(BaseModel):
    tabular_data: pd.DataFrame  # we should do additional typing here...

    class Config:
        arbitrary_types_allowed = True


class TgaAnalysis(BaseModel):
    """Model to hold parameters from processed tga data"""

    nsteps: int = Field(description="number of program steps in the tga file")
    step_boundaries: Optional[List[Tuple[int, int]]] = Field(
        description="the starting and ending indices of each step in the tga file"
    )

    weight_change_temp_1percent: float
    weight_change_temp_5percent: float
    weight_change_temp_10percent: float
    max_weight_change_temp: Optional[float]
    max_weight_change_slope: Optional[float]
    max_weight_change_relweight: Optional[float]
    onset_temperature: Optional[float]

    @validator("step_boundaries")
    def check_boundaries_length(cls, v, values):
        if "nsteps" in values and len(v) != values["nsteps"]:
            raise ValueError(f"Expected {values['nsteps']} step boundaries, got {len(v)}")
        return v
