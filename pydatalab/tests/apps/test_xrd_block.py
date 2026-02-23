from pathlib import Path

import pytest

from pydatalab.apps.nexus.utils import NeXusValidationError, load_nexus_file
from pydatalab.apps.xrd.blocks import XRDBlock
from pydatalab.apps.xrd.utils import XRD_COLUMN_MAPPING, validate_xrd_columns

XRD_DATA_DIR = Path(__file__).parent.parent.parent / "example_data" / "XRD"
XRD_DATA_FILES = list(XRD_DATA_DIR.glob("*"))

# NXS files that are expected to fail XRD loading for specific reasons
# Maps filename -> (exception type, expected message fragment)
INVALID_NXS_FILES = {
    "chopper.nxs": (
        NeXusValidationError,
        "does not contain XRD-compatible data",
    ),
    "i11-1-116482_processed_251003_095210.nxs": (
        RuntimeError,
        "No NXdata groups found in the NeXus file",
    ),
}


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
        if f.name in INVALID_NXS_FILES:  # tested separately in test_invalid_nxs_files_raise
            return
        df, y_options, metadata = XRDBlock.load_pattern(f)
        assert all(y in df.columns for y in y_options)


def test_event():
    block = XRDBlock(item_id="test-id")
    assert block.data["wavelength"] == 1.54060
    block.process_events({"event_name": "set_wavelength", "wavelength": 1.0})
    assert block.data["wavelength"] == 1.0
    block.process_events({"event_name": "set_wavelength", "wavelength": None})
    assert block.data["wavelength"] == 1.54060
    block.process_events({"event_name": "set_wavelength", "wavelength": -1.0})
    assert len(block.data["errors"]) == 1
    assert block.data["wavelength"] == 1.54060


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_single_plots(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
        if f.name in INVALID_NXS_FILES:  # tested separately in test_invalid_nxs_files_raise
            return
        block = XRDBlock(item_id="test")
        block.generate_xrd_plot(f)
        assert block.data["bokeh_plot_data"]


@pytest.mark.parametrize("filename,error_info", list(INVALID_NXS_FILES.items()))
def test_invalid_nxs_files_raise(filename, error_info):
    """Check that known-invalid .nxs files raise the expected error with the expected message."""
    expected_error, expected_message = error_info
    with pytest.raises(expected_error, match=expected_message):
        load_nexus_file(
            str(XRD_DATA_DIR / filename),
            validator=validate_xrd_columns,
            column_mapping=XRD_COLUMN_MAPPING,
        )


@pytest.mark.parametrize(
    "filename,expected_cols,expected_rows",
    [
        ("i11-1-116513_processed_250929_135434.nxs", ["twotheta", "intensity"], 5000),
    ],
)
def test_valid_nxs_files_load(filename, expected_cols, expected_rows):
    """Check that known-good XRD .nxs files load with the correct columns and row counts."""
    df = load_nexus_file(
        str(XRD_DATA_DIR / filename),
        validator=validate_xrd_columns,
        column_mapping=XRD_COLUMN_MAPPING,
    )
    assert list(df.columns) == expected_cols
    assert len(df) == expected_rows
