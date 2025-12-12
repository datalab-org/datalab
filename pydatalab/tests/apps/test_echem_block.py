from pathlib import Path

import pytest
from navani.echem import echem_file_loader

from pydatalab.apps.echem.utils import (
    compute_gpcl_differential,
    filter_df_by_cycle_index,
    reduce_echem_cycle_sampling,
)


@pytest.fixture
def echem_dataframe():
    """Yields example echem data as a dataframe."""
    df = echem_file_loader(
        Path(__file__)
        .parent.joinpath(
            "../../example_data/echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
        )
        .resolve()
    )

    keys_with_units = {
        "Time": "time (s)",
        "Voltage": "voltage (V)",
        "Capacity": "capacity (mAh)",
        "Current": "current (mA)",
        "Charge Capacity": "charge capacity (mAh)",
        "Discharge Capacity": "discharge capacity (mAh)",
        "dqdv": "dQ/dV (mA/V)",
        "dvdq": "dV/dQ (V/mA)",
    }

    df.rename(columns=keys_with_units, inplace=True)
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
