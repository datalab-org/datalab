from pathlib import Path

import pytest

from pydatalab.apps.xrd.blocks import XRDBlock


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "XRD").glob("*")


def test_load(data_files):
    for f in data_files:
        df, y_options = XRDBlock.load_pattern(f)
        assert all(y in df.columns for y in y_options)
