from pathlib import Path

import pytest

from pydatalab.apps.raman.blocks import RamanBlock


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "raman").glob("*")


def test_load(data_files):
    for f in data_files:
        df, metadata, y_options = RamanBlock.load(f)
        assert all(y in df.columns for y in y_options)
