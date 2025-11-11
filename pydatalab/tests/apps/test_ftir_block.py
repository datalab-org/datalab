from pathlib import Path

import pytest

from pydatalab.apps.ftir import FTIRBlock


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


class TestFTIRAspFormat:
    """Tests for .asp file format from Agilent Spectrometer"""

    def test_load_asp(self, asp_file):
        """Test parsing of .asp format file"""
        df, xunits, yunits = FTIRBlock.parse_ftir_asp(asp_file)
        assert len(df) == 1932
        assert all(x in df.columns for x in ["Wavenumber", "Absorbance"])
        assert df["Wavenumber"].min() == pytest.approx(400.688817501068, 1e-5)
        assert df["Wavenumber"].max() == pytest.approx(3999.43349933624, 1e-5)
        assert df["Absorbance"].argmin() == 987
        assert df["Absorbance"].argmax() == 1928
        assert xunits == "default"
        assert yunits == "default"
        # Checking height of peak at 1079 cm-1 has correct height
        mask = (df["Wavenumber"] > 800) & (df["Wavenumber"] < 1500)
        assert max(df["Absorbance"][mask]) == pytest.approx(0.0536771319493808, 1e-5)

    def test_plot_asp(self, asp_file):
        """Test plotting of .asp format data"""
        ftir_data, xunits, yunits = FTIRBlock.parse_ftir_asp(asp_file)
        # _format_ftir_plot is a static method
        layout = FTIRBlock._format_ftir_plot(ftir_data, xunits, yunits)
        assert layout


class TestFTIRTxtFormat:
    """Tests for .txt file format from Shimadzu IR Tracer-100"""

    def test_load_txt(self, txt_file):
        """Test parsing of .txt format file"""
        df, xunits, yunits = FTIRBlock.parse_ftir_txt(txt_file)
        assert len(df) == 1868  # Number of data lines in the file
        assert all(x in df.columns for x in ["Wavenumber", "Absorbance"])
        assert df["Wavenumber"].min() == pytest.approx(399.264912, 1e-5)
        assert df["Wavenumber"].max() == pytest.approx(4000.364384, 1e-5)
        assert df["Absorbance"].min() == pytest.approx(55.6689, 1e-4)
        # Units from Shimadzu format
        assert xunits == "1/CM\n"
        assert yunits == "%T\n"

    def test_plot_txt(self, txt_file):
        """Test plotting of .txt format data"""
        ftir_data, xunits, yunits = FTIRBlock.parse_ftir_txt(txt_file)
        # _format_ftir_plot is a static method
        layout = FTIRBlock._format_ftir_plot(ftir_data, xunits, yunits)
        assert layout
