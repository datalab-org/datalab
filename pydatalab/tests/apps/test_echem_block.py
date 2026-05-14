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
    raw_df, _ = block._load_and_cache_echem(src, None, None, reload=True)
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


def test_load_and_cache_mpr_exports_bdf_csv_and_parquet(tmp_path):
    """Test that loading an .mpr file generates both a .bdf.csv download and .bdf.parquet cache."""
    import shutil

    import pandas as pd

    block = CycleBlock(item_id="test")
    src = shutil.copy(MPR_FILE, tmp_path / MPR_FILE.name)
    location = Path(src)
    parquet_path = location.with_name(location.stem + "_cached.bdf.parquet")
    csv_path = location.with_name(location.stem + ".bdf.csv")

    raw_df, returned_csv_path = block._load_and_cache_echem(
        location, parquet_path, csv_path, reload=True
    )

    assert returned_csv_path is not None
    assert returned_csv_path.exists()
    csv_columns = set(returned_csv_path.open().readline().strip().split(","))
    assert BDF_REQUIRED_COLUMNS.issubset(csv_columns)
    assert not {"Time", "Voltage", "Current", "Capacity", "state"}.intersection(csv_columns)

    assert parquet_path.exists()
    cached = pd.read_parquet(parquet_path)
    assert BDF_REQUIRED_COLUMNS.issubset(set(cached.columns))
    assert not {"Time", "Voltage", "Current", "Capacity", "state"}.intersection(cached.columns)

    assert not location.with_suffix(".RAW_PARSED.pkl").exists()
    assert len(raw_df) > 0


def test_load_and_cache_reads_from_bdf_parquet(tmp_path):
    """Test that a second load uses the .bdf.parquet cache instead of re-parsing."""
    import shutil

    block = CycleBlock(item_id="test")
    src = shutil.copy(MPR_FILE, tmp_path / MPR_FILE.name)
    location = Path(src)
    parquet_path = location.with_name(location.stem + "_cached.bdf.parquet")
    csv_path = location.with_name(location.stem + ".bdf.csv")

    # First load: parse and cache
    raw_df_first, _ = block._load_and_cache_echem(location, parquet_path, csv_path, reload=True)

    # Remove the source file to prove the second load uses the parquet cache
    location.unlink()
    raw_df_cached, returned_csv_path = block._load_and_cache_echem(
        location, parquet_path, csv_path, reload=False
    )

    assert returned_csv_path is not None
    assert len(raw_df_cached) == len(raw_df_first)


def test_load_and_cache_bdf_csv_source_caches_parquet_but_skips_csv(tmp_path):
    """Test that loading a .bdf.csv source writes a .bdf.parquet cache but no redundant .bdf.csv."""
    import shutil

    block = CycleBlock(item_id="test")
    src = Path(shutil.copy(BDF_CSV_FILE, tmp_path / BDF_CSV_FILE.name))
    bare_stem = Path(BDF_CSV_FILE.name).stem.removesuffix(".bdf")
    parquet_path = src.with_name(f"{bare_stem}_cached.bdf.parquet")

    raw_df, returned_csv_path = block._load_and_cache_echem(src, parquet_path, None, reload=True)

    assert returned_csv_path is None
    assert parquet_path.exists()
    assert len(raw_df) > 0


def test_load_and_cache_multi_file_stitch(tmp_path):
    """Test that stitching an .mpr and a .bdf.csv produces a merged .bdf.csv and .bdf.parquet."""
    import shutil

    import pandas as pd

    block = CycleBlock(item_id="test")
    mpr_src = Path(shutil.copy(MPR_FILE, tmp_path / MPR_FILE.name))
    bdf_src = Path(shutil.copy(BDF_CSV_FILE, tmp_path / BDF_CSV_FILE.name))

    cache_location = tmp_path / "merged_test"
    parquet_path = cache_location.with_name(cache_location.name + "_cached.bdf.parquet")
    csv_path = cache_location.with_name(cache_location.name + ".bdf.csv")

    raw_df, returned_csv_path = block._load_and_cache_echem(
        cache_location, parquet_path, csv_path, reload=True, locations=[mpr_src, bdf_src]
    )

    assert returned_csv_path is not None
    assert returned_csv_path.exists()
    csv_columns = set(returned_csv_path.open().readline().strip().split(","))
    assert BDF_REQUIRED_COLUMNS.issubset(csv_columns)
    assert not {"Time", "Voltage", "Current", "Capacity", "state"}.intersection(csv_columns)

    assert parquet_path.exists()
    cached = pd.read_parquet(parquet_path)
    assert BDF_REQUIRED_COLUMNS.issubset(set(cached.columns))
    assert not {"Time", "Voltage", "Current", "Capacity", "state"}.intersection(cached.columns)

    assert len(raw_df) > 0
    assert not cache_location.with_suffix(".RAW_PARSED.pkl").exists()


def test_save_bdf_exception_logs_warning_and_returns_none(tmp_path, caplog):
    """Test that _save_bdf catches export exceptions, logs a warning, and returns None."""
    import logging
    from unittest.mock import patch

    import pandas as pd

    from pydatalab.logger import LOGGER

    block = CycleBlock(item_id="test")
    parquet_path = tmp_path / "dummy.bdf.parquet"
    csv_path = tmp_path / "dummy.bdf.csv"
    dummy_df = pd.DataFrame({"Time": [0, 1], "Voltage": [3.0, 3.5], "Current": [1.0, 1.0]})

    LOGGER.addHandler(caplog.handler)
    try:
        with (
            caplog.at_level(logging.WARNING, logger="pydatalab"),
            patch(
                "pydatalab.apps.echem.blocks.export_to_bdf",
                side_effect=Exception("export failed"),
            ),
        ):
            result = block._save_bdf(dummy_df, parquet_path, csv_path)
    finally:
        LOGGER.removeHandler(caplog.handler)

    assert result is None
    assert not parquet_path.exists()
    assert not csv_path.exists()
    assert "Failed to export BDF csv file" in caplog.text


@pytest.mark.parametrize(
    "state_dtype",
    [
        # object dtype: what most navani parsers (e.g. Biologic .mpr) actually produce
        "object",
        # category dtype: produced by some navani pathways; pyarrow rejects mixed-type categories
        "category",
    ],
)
def test_save_bdf_mixed_type_state_column(tmp_path, state_dtype):
    """Test that _save_bdf handles a mixed int/str state column (0, 1, 'R') for both
    object and category dtypes.

    navani produces a `state` column with values 0 (charge), 1 (discharge), and 'R' (rest).
    Most parsers (e.g. Biologic .mpr) produce object dtype; some pathways produce category dtype.
    The category case has heterogeneous category values that pyarrow cannot serialise directly.
    The fix casts both object and category columns to str before writing parquet.
    """
    import pandas as pd

    block = CycleBlock(item_id="test")
    parquet_path = tmp_path / "test_cached.bdf.parquet"
    csv_path = tmp_path / "test.bdf.csv"

    raw_values = [0, 1, "R", 0, 1]
    state = pd.Categorical(raw_values) if state_dtype == "category" else raw_values
    raw_df = pd.DataFrame(
        {
            "Time": [0.0, 1.0, 2.0, 3.0, 4.0],
            "Voltage": [3.0, 3.5, 3.5, 3.5, 3.0],
            "Current": [1.0, -1.0, 0.0, 1.0, -1.0],
            "Capacity": [0.1, 0.1, 0.0, 0.1, 0.1],
            "state": state,
            "half cycle": [0, 1, 1, 2, 3],
            "full cycle": [0, 0, 0, 1, 1],
        }
    )

    result = block._save_bdf(raw_df, parquet_path, csv_path)

    assert result == csv_path
    navani_cols = {"Time", "Voltage", "Current", "Capacity", "state"}

    assert csv_path.exists(), "CSV export was not written"
    csv_columns = set(csv_path.open().readline().strip().split(","))
    assert BDF_REQUIRED_COLUMNS.issubset(csv_columns)
    assert not navani_cols.intersection(csv_columns)

    assert parquet_path.exists(), "Parquet cache was not written"
    cached = pd.read_parquet(parquet_path)
    assert len(cached) == len(raw_df)
    assert BDF_REQUIRED_COLUMNS.issubset(set(cached.columns))
    assert not navani_cols.intersection(cached.columns)
