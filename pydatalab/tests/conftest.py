from pathlib import Path

import pytest


@pytest.fixture(scope="module", name="default_filepath")
def fixture_default_filepath():
    return Path(__file__).parent.joinpath(
        "../example_data/echem/jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
    )
