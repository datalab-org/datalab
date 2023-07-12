from typing import List, Optional

from pydantic import BaseModel

__all__ = ("RamanPattern", "RamanMeasurement")


class RamanPattern(BaseModel):
    """This model defines the structure of the data that is expected
    for a solid-state XRD pattern.

    """

    # wavelength: float

    # two_theta: List[float]

    wavenumber : List[float]

    # d_spacings: List[float]

    # q_values: List[float]

    intensities: List[float]


class RamanProcessing(BaseModel):

    peak_positions: List[float]

    peak_intensities: List[float]

    peak_widths: List[float]

    baselines: List[List[float]]

    class Config:
        extra = "allow"


class RamanMetadata(BaseModel):
    ...


class RamanMeasurement(BaseModel):

    data: Optional[RamanPattern]
    processing: Optional[RamanProcessing]
    metadata: Optional[RamanMetadata]
