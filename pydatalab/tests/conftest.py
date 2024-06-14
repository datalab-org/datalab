from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def example_data_dir():
    return Path(__file__).parent.parent / "example_data"


@pytest.fixture(scope="session", name="default_filepath")
def fixture_default_filepath(example_data_dir):
    return example_data_dir / "echem" / "jdb11-1_c3_gcpl_5cycles_2V-3p8V_C-24_data_C09.mpr"
