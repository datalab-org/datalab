from pydantic import BaseModel, Field

from pydatalab.models.blocks import DataBlockResponse


class CycleBlockComputed(BaseModel):
    """Extracted summary parameters from an electrochemical cycling dataset."""

    num_cycles: int
    """Maximum cycle index observed (excludes any rest-only cycle at index 0)."""

    initial_ce: float | None = None
    """Coulombic efficiency of the first non-rest cycle (discharge / charge capacity)."""

    final_capacity_mAh: float | None = None
    """Discharge capacity of the last cycle in mAh."""

    final_capacity_mAh_g: float | None = None
    """Discharge capacity of the last cycle in mAh/g (only set when characteristic mass is available)."""

    final_capacity_mAh_cm2: float | None = None
    """Discharge capacity of the last cycle in mAh/cm² (only set when electrode area is available)."""

    class Config:
        extra = "forbid"


class CycleBlockModel(DataBlockResponse):
    """Response model for the electrochemical cycling block."""

    blocktype: str = Field("cycle", const=True)

    computed: CycleBlockComputed | None = Field(default=None, datalab_exclude_from_load=True)
    """Extracted summary parameters from the cycling data."""
