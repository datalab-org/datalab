import zipfile
from pathlib import Path

import pytest

from pydatalab.apps.nmr.blocks import NMRBlock
from pydatalab.apps.nmr.utils import read_bruker_1d


def _extract_example(filename, dir):
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall(dir)
    return Path(dir) / filename.stem


@pytest.fixture(scope="function")
def nmr_1d_solution_path():
    yield Path(__file__).parent.parent.parent / "example_data" / "NMR" / "1.zip"


@pytest.fixture(scope="function")
def nmr_1d_solution_example(tmpdir, nmr_1d_solution_path):
    return _extract_example(nmr_1d_solution_path, tmpdir)


@pytest.fixture(scope="function")
def nmr_1d_solid_path():
    yield Path(__file__).parent.parent.parent / "example_data" / "NMR" / "71.zip"


@pytest.fixture(scope="function")
def nmr_1d_solid_example(tmpdir, nmr_1d_solid_path):
    return _extract_example(nmr_1d_solid_path, tmpdir)


@pytest.fixture(scope="function")
def nmr_2d_matpass_path():
    yield Path(__file__).parent.parent.parent / "example_data" / "NMR" / "72.zip"


@pytest.fixture(scope="function")
def nmr_2d_matpass_example(tmpdir, nmr_2d_matpass_path):
    return _extract_example(nmr_2d_matpass_path, tmpdir)


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


def test_nmr_block(nmr_1d_solution_path, nmr_1d_solid_path, nmr_2d_matpass_path):
    block = NMRBlock(item_id="nmr-block")
    block.read_bruker_nmr_data(nmr_1d_solid_path)
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "7Li 40 kHz 40 C hahn-echo"
    block.generate_nmr_plot(parse=False)
    plot = block.data["bokeh_plot_data"]
    assert plot is not None

    block = NMRBlock(item_id="nmr-block")
    block.read_bruker_nmr_data(nmr_1d_solution_path)
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "31P reference, 85% H3PO4"
    block.generate_nmr_plot(parse=False)
    plot = block.data["bokeh_plot_data"]
    assert plot is not None

    block = NMRBlock(item_id="nmr-block")
    block.read_bruker_nmr_data(nmr_2d_matpass_path)
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "7Li 40kHz 40 C MATPASS"
    # catch warning about processed data
    with pytest.warns(UserWarning, match="processed data"):
        block.generate_nmr_plot(parse=False)
        plot = block.data["bokeh_plot_data"]
        assert plot is None  # cannot plot MATPASS yet
