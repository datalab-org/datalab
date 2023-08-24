import zipfile
from pathlib import Path

import pytest

from pydatalab.apps.nmr.utils import read_bruker_1d


def _extract_example(filename, dir):
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall(dir)
    return Path(dir) / filename.stem


@pytest.fixture(scope="function")
def nmr_1d_solution_example(tmpdir):
    zip_path = Path(__file__).parent.parent.parent / "example_data" / "NMR" / "1.zip"
    return _extract_example(zip_path, tmpdir)


@pytest.fixture(scope="function")
def nmr_1d_solid_example(tmpdir):
    zip_path = Path(__file__).parent.parent.parent / "example_data" / "NMR" / "71.zip"
    return _extract_example(zip_path, tmpdir)


@pytest.fixture(scope="function")
def nmr_2d_matpass_example(tmpdir):
    zip_path = Path(__file__).parent.parent.parent / "example_data" / "NMR" / "72.zip"
    return _extract_example(zip_path, tmpdir)


def test_bruker_reader_solution(nmr_1d_solution_example):
    df, a_dic, topspin_title, shape = read_bruker_1d(nmr_1d_solution_example)
    assert df is not None
    assert a_dic
    assert topspin_title
    assert shape == (4096,)


def test_bruker_reader_solid(nmr_1d_solid_example):
    df, a_dic, topspin_title, shape = read_bruker_1d(nmr_1d_solid_example)
    assert df is not None
    assert a_dic
    assert topspin_title
    assert shape == (9984,)


def test_bruker_reader_2D(nmr_2d_matpass_example):
    df, a_dic, topspin_title, shape = read_bruker_1d(nmr_2d_matpass_example)
    assert df is None
    assert a_dic
    assert topspin_title
    assert shape == (8, 4096)
