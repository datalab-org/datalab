from pathlib import Path

import pytest

from pydatalab.apps.uvvis import UVVisBlock
from pydatalab.apps.uvvis.utils import find_absorbance, parse_uvvis_txt


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "UV-Vis").glob("*")


def test_load(data_files):
    for f in data_files:
        if f.suffix in UVVisBlock.accepted_file_extensions:
            df = parse_uvvis_txt(f)
            expected_columns = ["Wavelength", "Sample counts", "Dark counts", "Reference counts"]
            assert df is not None
            assert all(col in df.columns for col in expected_columns)
            assert df.shape[0] > 0
            assert df.shape[1] == len(expected_columns)


def test_find_absorbance(
    reference_file="1908047U1_0000.Raw8.TXT",
    sample_files=["1908047U1_0001.Raw8.txt", "1908047U1_0060.Raw8.txt"],
):
    # Tests two specific sample files with one reference file, will fail if files aren't present in the example data
    reference_path = (
        Path(__file__).parent.parent.parent / "example_data" / "UV-Vis" / reference_file
    )
    expected_columns = ["Wavelength", "Absorbance"]
    reference_df = None
    sample_dfs = []
    full_suffix = "".join(reference_path.suffixes).lower()
    if full_suffix in {ext.lower() for ext in UVVisBlock.accepted_file_extensions}:
        reference_df = parse_uvvis_txt(reference_path)

    for f in sample_files:
        f = Path(__file__).parent.parent.parent / "example_data" / "UV-Vis" / f
        full_suffix = "".join(f.suffixes).lower()
        if full_suffix in {ext.lower() for ext in UVVisBlock.accepted_file_extensions}:
            sample_dfs.append(parse_uvvis_txt(f))

    if reference_df is None:
        raise ValueError("Reference file '1908047U1_0000.Raw8.TXT' not found.")
    assert len(sample_dfs) > 0
    for df in sample_dfs:
        absorbance_df = find_absorbance(df, reference_df)
        assert absorbance_df is not None
        assert all(col in absorbance_df.columns for col in expected_columns)
        assert absorbance_df.shape[0] == df.shape[0]
        assert absorbance_df.shape[1] == 2  # Wavelength and Absorbance


def test_plot(
    reference_file="1908047U1_0000.Raw8.TXT",
    sample_files=["1908047U1_0001.Raw8.txt", "1908047U1_0060.Raw8.txt"],
):
    reference_path = (
        Path(__file__).parent.parent.parent / "example_data" / "UV-Vis" / reference_file
    )
    reference_df = None
    sample_dfs = []
    full_suffix = "".join(reference_path.suffixes).lower()
    if full_suffix in {ext.lower() for ext in UVVisBlock.accepted_file_extensions}:
        reference_df = parse_uvvis_txt(reference_path)

    for f in sample_files:
        f = Path(__file__).parent.parent.parent / "example_data" / "UV-Vis" / f
        full_suffix = "".join(f.suffixes).lower()
        if full_suffix in {ext.lower() for ext in UVVisBlock.accepted_file_extensions}:
            sample_dfs.append(parse_uvvis_txt(f))

    assert len(sample_dfs) > 0
    absorbance_dfs = []
    for df in sample_dfs:
        absorbance_dfs.append(find_absorbance(df, reference_df))
    layout = UVVisBlock._format_UV_Vis_plot(absorbance_dfs)
    assert layout
