from pydantic import BaseModel

from pydatalab.models.blocks import DataBlockResponse


class NMRMetadata(BaseModel):
    nucleus: str
    """The nucleus being observed in the NMR experiment (e.g., '1H', '13C', etc.)."""

    acquisition_parameters: dict | None = None
    """Dictionary containing acquisition parameters such as acquisition time, spectral width, etc."""

    processing_parameters: dict | None = None
    """Dictionary containing processing parameters such as apodization, zero-filling, etc."""

    pulse_program: dict | None = None
    """Dictionary containing details about the pulse program used for the NMR experiment."""

    carrier_frequency_MHz: float | None = None
    """The carrier frequency in MHz used during the NMR experiment."""

    spectral_window_Hz: float | None = None
    """The spectral window in Hz used during the NMR experiment."""

    carrier_offset_Hz: float | None = None
    """The carrier offset in Hz used during the NMR experiment."""

    recycle_delay: float | None = None
    """The recycle delay in seconds used during the NMR experiment."""

    nscans: int | None = None
    """The number of scans used during the NMR experiment."""

    CNST31: float | None = None
    """The CNST31 parameter used during the NMR experiment."""

    processed_data_shape: tuple[int, ...] | None = None
    """Tuple representing the shape of the processed NMR data array."""

    probe_name: str | None = None
    """Name of the probe used in the NMR experiment."""

    pulse_program_name: str | None = None
    """Name of the pulse program used in the NMR experiment."""

    title: str | None = None
    """Title or description of the NMR experiment."""

    class Config:
        extra = "forbid"


class NMRModel(DataBlockResponse):
    metadata: NMRMetadata | None = None
