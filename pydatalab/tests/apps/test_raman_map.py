from pathlib import Path

import pytest

from pydatalab.apps.raman_map.blocks import RamanMapBlock


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "raman").glob("*map.wdf")


def test_load(data_files):
    for f in data_files:
        spectra, data, metadata = RamanMapBlock.load(f)
        map = data["data"]
        assert spectra.shape == (1011,)
        assert map.shape == (5, 7, 1011)
        assert "General" in metadata
        assert "Signal" in metadata
        assert "Acquisition_instrument" in metadata

        RamanMapBlock.plot_raman_map(f)
