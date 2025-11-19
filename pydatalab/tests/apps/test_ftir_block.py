from pathlib import Path

import pytest


@pytest.fixture
def asp_file():
    """Fixture for .asp format file from Agilent Spectrometer"""
    return (
        Path(__file__).parent.parent.parent / "example_data" / "FTIR" / "2024-10-10_FeSO4_ref.asp"
    )


@pytest.fixture
def txt_file():
    """Fixture for .txt format file from Shimadzu IR Tracer-100"""
    return Path(__file__).parent.parent.parent / "example_data" / "FTIR" / "[FTIRText]020.txt"


def test_load_asp(asp_file):
    """Test parsing of .asp format file"""
    from pydatalab.apps.ftir import FTIRBlock

    df = FTIRBlock.parse_ftir_asp(asp_file)
    assert len(df) == 1932
    assert all(x in df.columns for x in ["Wavenumber (cm⁻¹)", "Absorbance (%)"])
    assert df["Wavenumber (cm⁻¹)"].min() == pytest.approx(400.688817501068, 1e-5)
    assert df["Wavenumber (cm⁻¹)"].max() == pytest.approx(3999.43349933624, 1e-5)
    assert df["Absorbance (%)"].argmin() == 987
    assert df["Absorbance (%)"].argmax() == 1928
    # Checking height of peak at 1079 cm-1 has correct height
    mask = (df["Wavenumber (cm⁻¹)"] > 800) & (df["Wavenumber (cm⁻¹)"] < 1500)
    assert max(df["Absorbance (%)"][mask]) == pytest.approx(5.36771319493808, 1e-5)


def test_plot_asp(asp_file):
    """Test plotting of .asp format data"""
    from pydatalab.apps.ftir import FTIRBlock

    ftir_data = FTIRBlock.parse_ftir_asp(asp_file)
    layout = FTIRBlock._format_ftir_plot(ftir_data)
    assert layout


def test_load_txt(txt_file):
    """Test parsing of .txt format file"""
    from pydatalab.apps.ftir import FTIRBlock

    df = FTIRBlock.parse_ftir_txt(txt_file)
    assert len(df) == 27  # Number of data lines in the file
    assert all(x in df.columns for x in ["Wavenumber (cm⁻¹)", "Absorbance (%)"])
    assert df["Wavenumber (cm⁻¹)"].min() == pytest.approx(399.264912, 1e-5)
    assert df["Wavenumber (cm⁻¹)"].max() == pytest.approx(449.414128, 1e-5)
    assert df["Absorbance (%)"].min() == pytest.approx(81.708257, 1e-4)
    assert df.attrs["title"] == "No Description"


def test_plot_txt(txt_file):
    """Test plotting of .txt format data"""
    from pydatalab.apps.ftir import FTIRBlock

    ftir_data = FTIRBlock.parse_ftir_txt(txt_file)
    layout = FTIRBlock._format_ftir_plot(ftir_data)
    assert layout
