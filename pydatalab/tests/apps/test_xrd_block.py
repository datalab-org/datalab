from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import XRDBlock
from pydatalab.apps.xrd.utils import parse_bruker_raw

XRD_DATA_FILES = list((Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*"))


@pytest.mark.parametrize("f", XRD_DATA_FILES)
def test_load(f):
    if f.suffix in XRDBlock.accepted_file_extensions:
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
        block = XRDBlock(item_id="test")
        block.generate_xrd_plot(f)
        assert block.data["bokeh_plot_data"]


@pytest.mark.parametrize("missing_steps", [1, 25, 250, 1000])
def test_truncated_bruker_raw(tmp_path, missing_steps):
    """An incomplete .raw file (e.g., mid-measurement) should still parse,
    padding the missing intensities with NaN and warning about the partial read."""
    raw_file = next(f for f in XRD_DATA_FILES if f.suffix == ".raw")
    full_df, full_metadata = parse_bruker_raw(raw_file)
    nsteps = int(full_metadata["Nsteps"])

    truncated_file = tmp_path / raw_file.name
    truncated_file.write_bytes(raw_file.read_bytes()[: -4 * missing_steps])

    read_steps = nsteps - missing_steps
    with pytest.warns(
        UserWarning, match=f"could only read {read_steps} of {nsteps} expected steps"
    ):
        df, metadata = parse_bruker_raw(truncated_file)

    assert int(metadata["Nsteps"]) == nsteps
    assert len(df) == nsteps
    assert df["twotheta"].equals(full_df["twotheta"])
    assert df["intensity"].iloc[:read_steps].equals(full_df["intensity"].iloc[:read_steps])
    assert df["intensity"].iloc[read_steps:].isna().all()
