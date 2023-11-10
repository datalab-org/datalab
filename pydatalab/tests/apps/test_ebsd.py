from pathlib import Path

import pytest

from pydatalab.apps.ebsd.blocks import EBSDBlock


@pytest.fixture
def data_files():
    return (Path(__file__).parent.parent.parent / "example_data" / "ebsd").glob("*.ctf")


def test_load(data_files):
    for f in data_files:
        df, phases = EBSDBlock.load(f)
        assert not df.empty
        assert phases
        breakpoint()
