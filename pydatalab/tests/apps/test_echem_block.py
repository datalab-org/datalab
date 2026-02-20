from pathlib import Path

import pytest

from pydatalab.apps.echem.blocks import CycleBlock
from pydatalab.apps.echem.utils import (
    compute_gpcl_differential,
    filter_df_by_cycle_index,
    reduce_echem_cycle_sampling,
)

ECHEM_DATA_DIR = Path(__file__).parent.parent.parent / "example_data" / "echem"
MPR_FILE = ECHEM_DATA_DIR / "jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
BDF_CSV_FILE = ECHEM_DATA_DIR / "arbin_example.bdf.csv"
BDF_REQUIRED_COLUMNS = {"Test Time / s", "Voltage / V", "Current / A"}


@pytest.fixture
def echem_dataframe(tmp_path):
    """Yields example echem data as a dataframe, loaded via CycleBlock to mimic block behaviour."""
    import shutil

    src = Path(shutil.copy(MPR_FILE, tmp_path / MPR_FILE.name))
    block = CycleBlock(item_id="test")
    raw_df, _ = block._load_and_cache_echem(src, None, reload=True)
    df, _ = CycleBlock.process_raw_echem_df(raw_df, None)
    return df


@pytest.fixture
def reduced_echem_dataframe(echem_dataframe):
    return reduce_echem_cycle_sampling(echem_dataframe, 100)


@pytest.fixture
def reduced_and_filtered_echem_dataframe(reduced_echem_dataframe):
    return filter_df_by_cycle_index(reduced_echem_dataframe)


def test_reduce_size(echem_dataframe):
    original_size = echem_dataframe.shape[0]
    for size in (1, 10, int(0.5 * len(echem_dataframe)), len(echem_dataframe)):
        number_of_cycles = echem_dataframe["half cycle"].nunique()
        reduced_df = reduce_echem_cycle_sampling(echem_dataframe, size)
        assert size <= reduced_df.shape[0] <= (size + 1) * number_of_cycles
        assert echem_dataframe.shape[0] == original_size
        assert reduced_df.shape[1] == echem_dataframe.shape[1]


def test_compute_gpcl_differential(reduced_and_filtered_echem_dataframe):
    df = reduced_and_filtered_echem_dataframe

    dqdv_results = compute_gpcl_differential(df)
    assert "dQ/dV (mA/V)" in dqdv_results

    dvdq_results = compute_gpcl_differential(df, mode="dV/dQ")
    assert "dV/dQ (V/mA)" in dvdq_results


def test_filter_df_by_cycle_index(reduced_echem_dataframe):
    cycle_lists = ([1, 2, 3], [4.0, 6.0, 10.0], [-1, 5, 2])
    for cycle_list in cycle_lists:
        filtered_df = filter_df_by_cycle_index(reduced_echem_dataframe, cycle_list)
        assert {int(i) for i in filtered_df["full cycle"]}.issubset({int(i) for i in cycle_list})


def test_plot(reduced_echem_dataframe):
    from pydatalab.bokeh_plots import double_axes_echem_plot

    layout = double_axes_echem_plot([reduced_echem_dataframe])
    assert layout
    differential_df = compute_gpcl_differential(reduced_echem_dataframe, mode="dV/dQ")
    layout = double_axes_echem_plot([differential_df], mode="dV/dQ")
    assert layout


def test_load_and_cache_mpr_exports_bdf_csv(tmp_path):
    """Test that loading an .mpr file generates a .bdf.csv export alongside the pickle cache."""
    import shutil

    block = CycleBlock(item_id="test")
    # Copy the source file to tmp_path so cache files don't pollute the example_data directory
    src = shutil.copy(MPR_FILE, tmp_path / MPR_FILE.name)
    location = Path(src)
    bdf_path = location.with_name(location.stem + ".bdf.csv")

    raw_df, returned_bdf_path = block._load_and_cache_echem(location, bdf_path, reload=True)

    assert returned_bdf_path is not None
    assert returned_bdf_path.exists()
    assert BDF_REQUIRED_COLUMNS.issubset(set(returned_bdf_path.open().readline().split(",")))
    assert location.with_suffix(".RAW_PARSED.pkl").exists()
    assert len(raw_df) > 0


def test_load_and_cache_bdf_csv_source_skips_export(tmp_path):
    """Test that loading a .bdf.csv source file skips BDF export (bdf_path=None)."""
    import shutil

    block = CycleBlock(item_id="test")
    src = shutil.copy(BDF_CSV_FILE, tmp_path / BDF_CSV_FILE.name)
    location = Path(src)

    # bdf_path=None signals that the source is already BDF - no export should be attempted
    raw_df, returned_bdf_path = block._load_and_cache_echem(location, None, reload=True)

    assert returned_bdf_path is None
    assert len(raw_df) > 0


def test_load_and_cache_multi_file_stitch(tmp_path):
    """Test that stitching an .mpr and a .bdf.csv produces a merged pickle and .bdf.csv export."""
    import shutil

    block = CycleBlock(item_id="test")
    mpr_src = Path(shutil.copy(MPR_FILE, tmp_path / MPR_FILE.name))
    bdf_src = Path(shutil.copy(BDF_CSV_FILE, tmp_path / BDF_CSV_FILE.name))

    cache_location = tmp_path / "merged_test"
    bdf_path: Path | None = cache_location.with_name(cache_location.name + ".bdf.csv")

    raw_df, returned_bdf_path = block._load_and_cache_echem(
        cache_location, bdf_path, reload=True, locations=[mpr_src, bdf_src]
    )

    assert returned_bdf_path is not None
    assert returned_bdf_path.exists()
    assert len(raw_df) > 0
    # Pickle should also have been created
    assert cache_location.with_suffix(".RAW_PARSED.pkl").exists()
