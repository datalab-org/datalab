from pydantic import BaseModel

__all__ = ("PeakInformation",)


class PeakInformation(BaseModel):
    positions: list[float] | None = None
    intensities: list[float] | None = None
    widths: list[float] | None = None
    hkls: list[tuple[int, int, int]] | None = None
    theoretical: bool = False
