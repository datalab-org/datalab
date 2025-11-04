from pathlib import Path

import pytest

from pydatalab.apps.ftir import FTIRBlock


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "FTIR").glob("*")


def test_load(data_files):
    for f in data_files:
        df = FTIRBlock.parse_ftir_asp(f)
        assert len(df) == 1932
        assert all(x in df.columns for x in ["Wavenumber", "Absorbance"])
        assert df["Wavenumber"].min() == pytest.approx(400.688817501068, 1e-5)
        assert df["Wavenumber"].max() == pytest.approx(3999.43349933624, 1e-5)
        assert df["Absorbance"].argmin() == 987
        assert df["Absorbance"].argmax() == 1928
        # Checking height of peak at 1079 cm-1 has correct height
        mask = (df["Wavenumber"] > 800) & (df["Wavenumber"] < 1500)
        assert max(df["Absorbance"][mask]) == pytest.approx(0.0536771319493808, 1e-5)


def test_plot(data_files):
    f = next(data_files)
    ftir_data = FTIRBlock.parse_ftir_asp(f)
    layout = FTIRBlock._format_ftir_plot(ftir_data)
    assert layout
