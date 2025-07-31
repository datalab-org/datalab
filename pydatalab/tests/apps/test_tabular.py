import pytest

from pydatalab.blocks.common import TabularDataBlock


def test_load_raman_txt(example_data_dir):
    with pytest.warns(UserWarning):
        df = TabularDataBlock.load(example_data_dir / "raman" / "raman_example.txt")
    assert df.shape == (1011, 2)


def test_load_labspec_raman_txt(example_data_dir):
    with pytest.warns(UserWarning):
        df = TabularDataBlock.load(example_data_dir / "raman" / "labspec_raman_example.txt")
    assert df.shape == (341, 2)


def test_simple_csv(example_data_dir):
    df = TabularDataBlock.load(example_data_dir / "csv" / "simple.csv")
    assert df.shape == (2, 3)
    assert df.columns.tolist() == ["test", "test2", "test3"]


def test_simple_xlsx(example_data_dir):
    df = TabularDataBlock.load(example_data_dir / "csv" / "simple.xlsx")
    assert df.shape == (4, 4)
