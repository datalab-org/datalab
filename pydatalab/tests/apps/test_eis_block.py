"""Tests for the EIS text parsers, using small hand-written files."""

import pandas as pd
import pytest

from pydatalab.apps.eis.utils import (
    add_derived_eis_columns,
    parse_ivium_eis_txt,
    parse_ivium_eis_txt_no_header,
    parse_pstrace_eis_txt,
)


def test_pstrace_parse(tmp_path):
    path = tmp_path / "pstrace_eis.txt"
    path.write_text(
        "Frequency\tZdash\tZdashneg\tZ\tPhase\tY\tYRe\tYIm\tCdash\tCdashdash\n"
        "1000\t3\t4\t5\t-53.13\t0.2\t0.12\t0.16\t1e-6\t2e-6\n"
        "100\t6\t8\t10\t-53.13\t0.1\t0.06\t0.08\t1e-5\t2e-5\n"
    )
    df = parse_pstrace_eis_txt(path)
    assert list(df["Frequency [Hz]"]) == [1000, 100]
    assert list(df["Re(Z) [Ω]"]) == [3, 6]
    assert list(df["-Im(Z) [Ω]"]) == [4, 8]
    assert list(df["|Z| [Ω]"]) == [5, 10]
    assert list(df["log(Frequency) [Hz]"]) == pytest.approx([3, 2])


def test_pstrace_rejects_non_pstrace_file(tmp_path):
    path = tmp_path / "not_eis.txt"
    path.write_text("alpha\tbeta\n1\t2\n")
    with pytest.raises(RuntimeError, match="valid PSTrace EIS export"):
        parse_pstrace_eis_txt(path)


def test_ivium_negates_imaginary_part(tmp_path):
    path = tmp_path / "ivium_eis.txt"
    path.write_text("freq. /Hz\tZ1 /ohm\tZ2 /ohm\n1000\t3\t-4\n")
    df = parse_ivium_eis_txt(path)
    assert df["-Im(Z) [Ω]"].iloc[0] == 4
    assert df["|Z| [Ω]"].iloc[0] == pytest.approx(5.0)


def test_ivium_rejects_non_ivium_file(tmp_path):
    path = tmp_path / "not_eis.txt"
    path.write_text("alpha\tbeta\n1\t2\n")
    with pytest.raises(RuntimeError, match="valid Ivium EIS export"):
        parse_ivium_eis_txt(path)


def test_ivium_no_header_parse(tmp_path):
    path = tmp_path / "ivium_eis_no_header.txt"
    path.write_text("1000\t3\t4\n100\t6\t8\n")
    df = parse_ivium_eis_txt_no_header(path)
    assert list(df["Frequency [Hz]"]) == [1000, 100]
    assert list(df["-Im(Z) [Ω]"]) == [4, 8]


def test_ivium_no_header_rejects_headed_file(tmp_path):
    """A file with column names must not be read as headerless data."""
    path = tmp_path / "ivium_eis.txt"
    path.write_text("freq. /Hz\tZ1 /ohm\tZ2 /ohm\n1000\t3\t-4\n")
    with pytest.raises(RuntimeError, match="headerless Ivium EIS export"):
        parse_ivium_eis_txt_no_header(path)


def test_ivium_no_header_rejects_two_columns(tmp_path):
    path = tmp_path / "two_col.txt"
    path.write_text("1.0\t2.0\n3.0\t4.0\n")
    with pytest.raises(RuntimeError, match="headerless Ivium EIS export"):
        parse_ivium_eis_txt_no_header(path)


def test_derived_columns_do_not_overwrite_existing():
    df = pd.DataFrame(
        {
            "Frequency [Hz]": [1.0, 10.0],
            "Re(Z) [Ω]": [3.0, 3.0],
            "-Im(Z) [Ω]": [4.0, 4.0],
            "|Z| [Ω]": [999.0, 999.0],
        }
    )
    out = add_derived_eis_columns(df)
    assert list(out["|Z| [Ω]"]) == [999.0, 999.0]


def test_derived_phase_is_negative_for_capacitive_response():
    """-Im(Z) positive means Im(Z) negative, so θ must come out negative."""
    df = pd.DataFrame({"Frequency [Hz]": [1.0], "Re(Z) [Ω]": [3.0], "-Im(Z) [Ω]": [4.0]})
    out = add_derived_eis_columns(df)
    assert out["θ [°]"].iloc[0] == pytest.approx(-53.13010, abs=1e-4)
    assert out["|Z| [Ω]"].iloc[0] == pytest.approx(5.0)
