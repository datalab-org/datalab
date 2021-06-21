import pandas as pd
import numpy as np
from pathlib import Path
from pydatalab.blocks.echem_block import reduce_echem_cycle_sampling, compute_gpcl_differential
import pytest
from navani.echem import echem_file_loader


@pytest.fixture
def echem_dataframe():
    """Yields example echem data as a dataframe."""
    return echem_file_loader(
        Path(__file__).parent.joinpath("../../example_data/echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr").resolve()
    )


@pytest.fixture
def reduced_echem_dataframe(echem_dataframe):
    """Yields example echem data as a dataframe."""
    return reduce_echem_cycle_sampling(echem_dataframe, 100)


def test_reduce_size(echem_dataframe):
    original_size = echem_dataframe.shape[0]
    for size in (1, 10, int(0.5 * len(echem_dataframe)), len(echem_dataframe)):
        reduced_df = reduce_echem_cycle_sampling(
            echem_dataframe, size
        )
        assert size <= reduced_df.shape[0] <= size + 1
        assert echem_dataframe.shape[0] == original_size
        assert reduced_df.shape[1] == echem_dataframe.shape[1]

def test_compute_gpcl_differential(reduced_echem_dataframe):

    dqdv_results = compute_gpcl_differential(
        reduced_echem_dataframe,
        cycle_list=None,
    )

    assert "dqdv" in dqdv_results

    dvdq_results = compute_gpcl_differential(
        reduced_echem_dataframe,
        cycle_list=None,
        mode="dv/dq",
    )

    assert "dvdq" in dvdq_results
