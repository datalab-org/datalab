import shutil
import zipfile
from pathlib import Path

import pytest

from pydatalab.apps.nmr.blocks import NMRBlock
from pydatalab.apps.nmr.utils import read_bruker_1d, read_jcamp_dx_1d


def _extract_example(filename, _dir):
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall(_dir)
    return Path(_dir) / filename.stem


@pytest.fixture(scope="function")
def nmr_1d_solution_path():
    yield Path(__file__).parent.parent.parent / "example_data" / "NMR" / "1.zip"


@pytest.fixture(scope="function")
def nmr_1d_solution_path_renamed(tmpdir, nmr_1d_solution_path):
    """A renamed version of the 1D solution example, to test whether
    the process finder can handle mismatched file names."""
    new_path = Path(tmpdir / "2.zip")
    shutil.copy(nmr_1d_solution_path, new_path)
    yield new_path


@pytest.fixture(scope="function")
def nmr_1d_solution_example(tmpdir, nmr_1d_solution_path):
    return _extract_example(nmr_1d_solution_path, tmpdir)


@pytest.fixture(scope="function")
def nmr_jcamp_1h_path():
    yield Path(__file__).parent.parent.parent / "example_data" / "NMR" / "1h.dx"


@pytest.fixture(scope="function")
def nmr_jcamp_13c_path():
    yield Path(__file__).parent.parent.parent / "example_data" / "NMR" / "13c.jdx"


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


def test_nmr_block(
    nmr_1d_solution_path, nmr_1d_solution_path_renamed, nmr_1d_solid_path, nmr_2d_matpass_path
):
    block = NMRBlock(item_id="nmr-block")
    block.processed_data, block.data["metadata"] = block.read_bruker_nmr_data(nmr_1d_solid_path)
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "7Li 40 kHz 40 C hahn-echo"
    block.generate_nmr_plot(parse=False)
    plot = block.data["bokeh_plot_data"]
    assert plot is not None

    block = NMRBlock(item_id="nmr-block")
    block.processed_data, block.data["metadata"] = block.read_bruker_nmr_data(nmr_1d_solution_path)
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "31P reference, 85% H3PO4"
    block.generate_nmr_plot(parse=False)
    plot = block.data["bokeh_plot_data"]
    assert plot is not None

    block = NMRBlock(item_id="nmr-block")
    block.processed_data, block.data["metadata"] = block.read_bruker_nmr_data(
        nmr_1d_solution_path_renamed
    )
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "31P reference, 85% H3PO4"
    block.generate_nmr_plot(parse=False)
    plot = block.data["bokeh_plot_data"]
    assert plot is not None

    block = NMRBlock(item_id="nmr-block")
    block.processed_data, block.data["metadata"] = block.read_bruker_nmr_data(nmr_2d_matpass_path)
    assert block.data["metadata"]["topspin_title"].split("\n")[0] == "7Li 40kHz 40 C MATPASS"
    # catch warning about processed data
    with pytest.warns(UserWarning, match="Only metadata"):
        block.generate_nmr_plot(parse=False)
        plot = block.data.get("bokeh_plot_data")
        assert plot is None  # cannot plot MATPASS yet


def test_read_jcamp_1h_1d(nmr_jcamp_1h_path):
    df, dic, title, shape = read_jcamp_dx_1d(nmr_jcamp_1h_path)
    assert df is not None
    assert dic[".OBSERVENUCLEUS"]

    block = NMRBlock(item_id="nmr-block")
    block.read_jcamp_nmr_data(nmr_jcamp_1h_path)
    assert block.data["metadata"]["title"] == title
    assert block.data["metadata"]["nucleus"] == "1H"
    assert block.data["metadata"]["carrier_frequency_Hz"] == 400.4224e6


def test_read_jcamp_13c_1d(nmr_jcamp_13c_path):
    df, dic, title, shape = read_jcamp_dx_1d(nmr_jcamp_13c_path)
    assert df is not None
    assert dic[".OBSERVENUCLEUS"]

    block = NMRBlock(item_id="nmr-block")
    block.read_jcamp_nmr_data(nmr_jcamp_13c_path)
    assert block.data["metadata"]["title"] == title
    assert block.data["metadata"]["nucleus"] == "13C"
    assert block.data["metadata"]["carrier_frequency_Hz"] == 100.695689e6
