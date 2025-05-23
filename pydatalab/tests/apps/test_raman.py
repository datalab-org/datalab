from pathlib import Path

import numpy as np
import pytest

from pydatalab.apps.raman.blocks import RamanBlock


@pytest.fixture
def wdf_example():
    return Path(__file__).parent.parent.parent / "example_data" / "raman" / "raman_example.wdf"


@pytest.fixture
def labspec_txt_example():
    return (
        Path(__file__).parent.parent.parent / "example_data" / "raman" / "labspec_raman_example.txt"
    )


@pytest.fixture
def renishaw_txt_example():
    return Path(__file__).parent.parent.parent / "example_data" / "raman" / "raman_example.txt"


def test_load_wdf(wdf_example):
    df, metadata, y_options = RamanBlock.load(wdf_example)
    assert all(y in df.columns for y in y_options)
    assert df.shape == (1011, 11)
    np.testing.assert_almost_equal(df["intensity"].mean(), 364.29358, decimal=5)
    np.testing.assert_almost_equal(df["normalized intensity"].max(), 1.0, decimal=5)

    # TODO It is likely this is the "real" value we should be reading, but after switching to the older
    # package, we now longer have access to the offset.
    # np.testing.assert_almost_equal(
    #     df["wavenumber"][np.argmax(df["intensity"])], 1587.546335309901, decimal=5
    # )
    # np.testing.assert_almost_equal(df["wavenumber"].min(), 44.812868, decimal=5)
    # np.testing.assert_almost_equal(df["wavenumber"].max(), 1919.855951, decimal=5)
    np.testing.assert_almost_equal(
        df["wavenumber"][np.argmax(df["intensity"])], 1581.730469, decimal=5
    )
    np.testing.assert_almost_equal(df["wavenumber"].min(), 0.380859, decimal=5)
    np.testing.assert_almost_equal(df["wavenumber"].max(), 1879.449219, decimal=5)


def test_load_renishaw_txt(renishaw_txt_example):
    with pytest.warns(UserWarning, match="Unable to find wavenumber unit"):
        with pytest.warns(UserWarning, match="Unable to find wavenumber offset"):
            df, metadata, y_options = RamanBlock.load(renishaw_txt_example)
    assert all(y in df.columns for y in y_options)
    assert df.shape == (1011, 11)
    np.testing.assert_almost_equal(df["intensity"].mean(), 364.293613265, decimal=5)
    np.testing.assert_almost_equal(df["normalized intensity"].max(), 1.0, decimal=5)
    np.testing.assert_almost_equal(
        df["wavenumber"][np.argmax(df["intensity"])], 1581.730469, decimal=5
    )

    np.testing.assert_almost_equal(df["wavenumber"].min(), 0.380859, decimal=5)
    np.testing.assert_almost_equal(df["wavenumber"].max(), 1879.449219, decimal=5)


def test_load_labspec_txt(labspec_txt_example):
    df, metadata, y_options = RamanBlock.load(labspec_txt_example)
    assert all(y in df.columns for y in y_options)
    assert df.shape == (341, 11)
    np.testing.assert_almost_equal(df["normalized intensity"].max(), 1.0, decimal=5)
