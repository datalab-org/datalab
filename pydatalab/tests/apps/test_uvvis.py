import logging
from pathlib import Path

import pytest

from pydatalab.apps.uvvis import UVVisBlock


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "UV-Vis").glob("*")


def test_load(data_files):
    logging.info("Testing UV-Vis data loading")
    for f in data_files:
        logging.info(f"Testing file: {f}")
        if f.suffix in UVVisBlock.accepted_file_extensions:
            logging.info(f"Loading file: {f}")
            df = UVVisBlock.parse_uvvis_txt(f)
            expected_columns = ["Wavelength", "Sample counts", "Dark counts", "Reference counts"]
            assert df is not None
            assert all(col in df.columns for col in expected_columns)
            assert df.shape[0] > 0
            assert df.shape[1] == len(expected_columns)


def test_find_absorbance(data_files):
    expected_columns = ["Wavelength", "Absorbance"]
    reference_df = None
    sample_dfs = []
    for f in data_files:
        if f.suffix in UVVisBlock.accepted_file_extensions:
            logging.info(f"Loading file: {f.name}")
            if f.name == "1908047U1_0000.Raw8(1).TXT":
                logging.info(f"Loading reference file: {f.name}")
                reference_df = UVVisBlock.parse_uvvis_txt(f)
            elif f.name == "1908047U1_0001.Raw8(1).txt" or f.name == "1908047U1_0060.Raw8.txt":
                sample_dfs.append(UVVisBlock.parse_uvvis_txt(f))
    if reference_df is None:
        raise ValueError("Reference file '1908047U1_0000.Raw8(1).TXT' not found.")

    for df in sample_dfs:
        absorbance_df = UVVisBlock.find_absorbance(df, reference_df)
        assert absorbance_df is not None
        assert all(col in absorbance_df.columns for col in expected_columns)
        assert absorbance_df.shape[0] == df.shape[0]
        assert absorbance_df.shape[1] == 2  # Wavelength and Absorbance


def test_plot(data_files):
    sample_dfs = []
    for f in data_files:
        if f.suffix in UVVisBlock.accepted_file_extensions:
            if f.name == "1908047U1_0000.Raw8(1).TXT":
                reference_df = UVVisBlock.parse_uvvis_txt(f)
            elif f.name == "1908047U1_0001.Raw8(1).txt" or f.name == "1908047U1_0060.Raw8.txt":
                sample_dfs.append(UVVisBlock.parse_uvvis_txt(f))

    absorbance_dfs = []
    for df in sample_dfs:
        absorbance_dfs.append(UVVisBlock.find_absorbance(df, reference_df))
    layout = UVVisBlock._format_UV_Vis_plot(absorbance_dfs)
    assert layout
