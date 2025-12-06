"""Tests for profiling (Wyko) data blocks and file readers."""

from pathlib import Path

import numpy as np
import pytest

from pydatalab.apps.profiling.blocks import ProfilingBlock
from pydatalab.apps.profiling.wyko_reader import (
    load_wyko_asc,
    parse_wyko_header,
)

# Look for example Wyko .ASC files in the example_data directory
PROFILING_DATA_DIR = Path(__file__).parent.parent.parent / "example_data" / "profiling"
WYKO_DATA_FILES = list(PROFILING_DATA_DIR.glob("*.ASC")) + list(PROFILING_DATA_DIR.glob("*.asc"))


# ============================================================================
# Fixtures - Load data once and reuse across tests
# ============================================================================


@pytest.fixture(scope="module", params=WYKO_DATA_FILES)
def wyko_file(request):
    """Fixture providing a Wyko file path."""
    f = request.param
    if not f.exists():
        pytest.skip(f"Test file not found: {f}")
    return f


@pytest.fixture(scope="module")
def wyko_metadata(wyko_file):
    """Fixture providing parsed metadata (cached for the module)."""
    return parse_wyko_header(wyko_file)


@pytest.fixture(scope="module")
def wyko_data(wyko_file):
    """Fixture providing loaded Wyko data without intensity (cached for the module)."""
    return load_wyko_asc(wyko_file, load_intensity=False, progress=False)


@pytest.fixture(scope="module")
def wyko_data_with_intensity(wyko_file, wyko_metadata):
    """Fixture providing loaded Wyko data with intensity if available (cached for the module).

    Returns None if the file doesn't have intensity data (avoiding wasted file I/O).
    Otherwise loads the file once with intensity and caches it for all tests in the module.
    """
    if wyko_metadata["intensity_start"] is None:
        return None
    return load_wyko_asc(wyko_file, load_intensity=True, progress=False)


# ============================================================================
# Wyko Reader Tests
# ============================================================================


def test_parse_wyko_header(wyko_metadata):
    """Test parsing Wyko ASC file headers."""
    # Check all expected keys are present
    assert "x_size" in wyko_metadata
    assert "y_size" in wyko_metadata
    assert "pixel_size" in wyko_metadata
    assert "raw_data_start" in wyko_metadata
    assert "intensity_start" in wyko_metadata

    # Check required fields are not None
    assert wyko_metadata["x_size"] is not None, "x_size should be parsed from header"
    assert wyko_metadata["y_size"] is not None, "y_size should be parsed from header"
    assert wyko_metadata["raw_data_start"] is not None, "raw_data_start should be found"

    # Check types
    assert isinstance(wyko_metadata["x_size"], int)
    assert isinstance(wyko_metadata["y_size"], int)
    assert isinstance(wyko_metadata["raw_data_start"], int)

    # Line numbers should be 1-indexed (positive integers)
    assert wyko_metadata["raw_data_start"] > 0


def test_load_wyko_asc_basic(wyko_data, wyko_metadata):
    """Test loading Wyko ASC files without intensity data."""
    # Check result structure
    assert "metadata" in wyko_data
    assert "raw_data" in wyko_data

    # Check metadata
    metadata = wyko_data["metadata"]
    assert metadata["x_size"] is not None
    assert metadata["y_size"] is not None

    # Check raw_data shape matches metadata
    raw_data = wyko_data["raw_data"]
    assert isinstance(raw_data, np.ndarray)
    assert raw_data.shape == (metadata["x_size"], metadata["y_size"])
    assert raw_data.dtype == np.float32  # Should use float32 for memory efficiency

    # Check that we have some valid (non-NaN) data
    valid_data = raw_data[~np.isnan(raw_data)]
    assert len(valid_data) > 0, "Should have some valid (non-NaN) data points"


def test_load_wyko_asc_with_intensity(wyko_file, wyko_metadata, wyko_data_with_intensity):
    """Test loading Wyko ASC files with intensity data if available."""
    if wyko_metadata["intensity_start"] is None:
        # File doesn't have intensity data - test error handling
        # This loads the file to verify the error is raised correctly.
        # The pytest.raises context manager executes the code inside and catches the expected error.
        with pytest.raises(
            ValueError, match="Intensity data requested but no Intensity block found"
        ):
            load_wyko_asc(wyko_file, load_intensity=True, progress=False)

        # Also verify the fixture correctly returned None (avoiding wasted load)
        assert wyko_data_with_intensity is None
    else:
        # File has intensity data - use the cached fixture
        result = wyko_data_with_intensity

        assert "metadata" in result
        assert "raw_data" in result
        assert "intensity" in result

        # Check intensity data shape matches raw_data
        assert result["intensity"].shape == result["raw_data"].shape
        assert result["intensity"].dtype == np.float32


# ============================================================================
# ProfilingBlock Tests
# ============================================================================


def test_profiling_block_accepted_extensions():
    """Test that ProfilingBlock has correct accepted file extensions."""
    assert ".asc" in ProfilingBlock.accepted_file_extensions


def test_profiling_block_metadata():
    """Test ProfilingBlock metadata."""
    assert ProfilingBlock.blocktype == "profiling"
    assert ProfilingBlock.name == "Surface Profiling"
    assert (
        "profilometry" in ProfilingBlock.description.lower()
        or "wyko" in ProfilingBlock.description.lower()
    )


def test_profiling_block_plot_generation(wyko_file):
    """Test that ProfilingBlock can generate plots from Wyko files."""
    block = ProfilingBlock(item_id="test")

    # Generate plot from file path directly (like XRD block does)
    block.generate_profiling_plot(wyko_file)

    # Verify that bokeh_plot_data was created
    assert "bokeh_plot_data" in block.data
    assert block.data["bokeh_plot_data"] is not None


# ============================================================================
# Test with conditional skip if no data files
# ============================================================================


def test_example_data_files_exist():
    """Informational test to show if example data files are present."""
    if not WYKO_DATA_FILES:
        pytest.skip(
            f"No Wyko .ASC files found in {PROFILING_DATA_DIR}. "
            "Tests will be skipped. To enable tests, add example .ASC files to "
            f"{PROFILING_DATA_DIR.relative_to(Path(__file__).parent.parent.parent)}"
        )
    else:
        # Just log the files we found
        print(f"\nFound {len(WYKO_DATA_FILES)} Wyko data file(s):")
        for f in WYKO_DATA_FILES:
            print(f"  - {f.name}")
