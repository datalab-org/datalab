from typing import List, Optional

from pydantic import BaseModel


class XRDPattern(BaseModel):
    """This model defines the structure of the data that is expected
    for a solid-state XRD pattern.

    """

    wavelength: float

    two_theta: List[float]

    d_spacings: List[float]

    q_values: List[float]

    intensities: List[float]


class XRDProcessing(BaseModel):

    peak_positions: List[float]

    peak_intensities: List[float]

    peak_widths: List[float]

    baselines: List[List[float]]

    class Config:
        extra = "allow"


class XRDMetadata(BaseModel):
    ...


class XRDMeasurement(BaseModel):

    data: Optional[XRDPattern]
    processing: Optional[XRDProcessing]
    metadata: Optional[XRDMetadata]
