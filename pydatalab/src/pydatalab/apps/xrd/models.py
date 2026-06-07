from pydantic import BaseModel

__all__ = ("PeakInformation", "XRDPattern")


class PeakInformation(BaseModel):
    positions: list[float] | None = None
    intensities: list[float] | None = None
    widths: list[float] | None = None
    hkls: list[tuple[int, int, int]] | None = None
    theoretical: bool = False


class XRDPattern(BaseModel):
    two_theta: list[float]
    intensity: list[float]
    error: list[float] | None = None
