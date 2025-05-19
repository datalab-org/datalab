from pydantic import BaseModel

__all__ = ("XRDPattern", "XRDMeasurement")


class XRDPattern(BaseModel):
    """This model defines the structure of the data that is expected
    for a solid-state XRD pattern.

    """

    wavelength: float

    two_theta: list[float]

    d_spacings: list[float]

    q_values: list[float]

    intensities: list[float]


class XRDProcessing(BaseModel):
    peak_positions: list[float]

    peak_intensities: list[float]

    peak_widths: list[float]

    baselines: list[list[float]]

    class Config:
        extra = "allow"


class XRDMetadata(BaseModel): ...


class XRDMeasurement(BaseModel):
    data: XRDPattern | None
    processing: XRDProcessing | None
    metadata: XRDMetadata | None
