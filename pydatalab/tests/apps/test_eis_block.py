"""Tests for the EIS block parsers.

No real instrument files are used. Every fixture in this module is written on
the fly from an analytic Randles equivalent circuit, in the same style as
``test_cv_block.py``. That keeps redistributable instrument exports out of the
repository and, more usefully, lets the *same* physical spectrum be written out
in more than one vendor's layout so the parsers can be checked against each
other rather than only against themselves.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pydatalab.apps.eis.utils import (
    _PSTRACE_COLUMN_MAP,
    add_derived_eis_columns,
    parse_ivium_eis_txt,
    parse_ivium_eis_txt_no_header,
    parse_pstrace_eis_txt,
)

# --- Synthetic spectrum -------------------------------------------------------

#: Randles cell: solution resistance in series with (charge transfer resistance
#: || double layer capacitance). Values are typical of a lab coin cell.
_RS_OHM = 12.5
_RCT_OHM = 240.0
_CDL_F = 2.2e-5

#: Instruments write a fixed number of significant figures. Six is a realistic
#: stand-in and sets the floor for how tightly anything read back can be compared.
_FLOAT_FORMAT = "%.6g"
_RTOL = 1e-5


def _randles_impedance(frequency_hz: np.ndarray) -> np.ndarray:
    """Complex impedance of a Randles cell at the given frequencies.

    Args:
        frequency_hz: Frequencies in Hz.

    Returns:
        Complex impedance in ohms, using the physics sign convention in which
        a capacitive response has a negative imaginary part.
    """
    omega = 2 * np.pi * frequency_hz
    z_cpe = 1.0 / (1j * omega * _CDL_F)
    return _RS_OHM + (_RCT_OHM * z_cpe) / (_RCT_OHM + z_cpe)


def _spectrum(n_points: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """Log-spaced frequency sweep from 100 kHz down to 0.1 Hz, as an EIS run is measured."""
    frequency = np.logspace(5, -1, n_points)
    return frequency, _randles_impedance(frequency)


# --- File writers -------------------------------------------------------------


def _make_pstrace_txt(tmp_path: Path, columns: list[str] | None = None) -> Path:
    """Write a tab-separated PSTrace-style EIS export.

    PSTrace lets the operator choose which columns leave the software ("EIS data
    export settings" in the PSTrace manual), so ``columns`` allows a partial
    export to be simulated.

    Args:
        tmp_path: Directory to write into.
        columns: Column names to include, defaulting to the full set that
            :data:`~pydatalab.apps.eis.utils._PSTRACE_COLUMN_MAP` expects.

    Returns:
        Path to the written file.
    """
    frequency, z = _spectrum()
    omega = 2 * np.pi * frequency
    y = 1.0 / z
    # PSTrace reports capacitance derived from admittance: C = Y / (jw)
    c = y / (1j * omega)

    available = {
        "Frequency": frequency,
        "Zdash": z.real,
        "Zdashneg": -z.imag,
        "Z": np.abs(z),
        "Phase": np.degrees(np.angle(z)),
        "Y": np.abs(y),
        "YRe": y.real,
        "YIm": y.imag,
        "Cdash": c.real,
        "Cdashdash": c.imag,
    }

    if columns is None:
        columns = list(_PSTRACE_COLUMN_MAP)

    df = pd.DataFrame({name: available[name] for name in columns})
    path = tmp_path / "pstrace_eis.txt"
    # Instruments write a handful of significant figures, not full float repr.
    # Writing at realistic precision keeps the tolerances below honest.
    df.to_csv(path, sep="\t", index=False, float_format=_FLOAT_FORMAT)
    return path


def _make_ivium_txt(tmp_path: Path) -> Path:
    """Write a tab-separated Ivium-style EIS export of the same spectrum.

    Ivium writes the imaginary part directly, which is why
    :func:`~pydatalab.apps.eis.utils.parse_ivium_eis_txt` negates it on the way in.
    """
    frequency, z = _spectrum()
    df = pd.DataFrame(
        {
            "freq. /Hz": frequency,
            "Z1 /ohm": z.real,
            "Z2 /ohm": z.imag,
        }
    )
    path = tmp_path / "ivium_eis.txt"
    df.to_csv(path, sep="\t", index=False, float_format=_FLOAT_FORMAT)
    return path


def _make_ivium_txt_no_header(tmp_path: Path) -> Path:
    """Write the headerless three-column Ivium variant."""
    frequency, z = _spectrum()
    path = tmp_path / "ivium_eis_no_header.txt"
    lines = [f"{f:.6g}\t{zr:.6g}\t{zi:.6g}\n" for f, zr, zi in zip(frequency, z.real, -z.imag)]
    path.write_text("".join(lines))
    return path


# --- PSTrace ------------------------------------------------------------------


def test_pstrace_renames_every_column(tmp_path):
    df = parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path))
    assert set(_PSTRACE_COLUMN_MAP.values()).issubset(df.columns)
    # None of the instrument's own names should survive the rename
    assert not set(_PSTRACE_COLUMN_MAP).intersection(df.columns)


def test_pstrace_values_round_trip(tmp_path):
    frequency, z = _spectrum()
    df = parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path))
    np.testing.assert_allclose(df["Frequency [Hz]"], frequency, rtol=_RTOL)
    np.testing.assert_allclose(df["Re(Z) [Ω]"], z.real, rtol=_RTOL)
    np.testing.assert_allclose(df["-Im(Z) [Ω]"], -z.imag, rtol=_RTOL)


def test_pstrace_keeps_instrument_magnitude_and_phase(tmp_path):
    """|Z| and θ must come from the instrument, not be recomputed over the top."""
    _, z = _spectrum()
    df = parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path))
    np.testing.assert_allclose(df["|Z| [Ω]"], np.abs(z), rtol=_RTOL)
    np.testing.assert_allclose(df["θ [°]"], np.degrees(np.angle(z)), rtol=_RTOL)


def test_pstrace_instrument_columns_are_self_consistent(tmp_path):
    """The instrument's |Z| and θ must agree with its own Re and Im columns.

    This is what makes a synthetic fixture worth anything: it pins the sign
    convention of the ``Phase`` column against the ``Zdash``/``Zdashneg`` pair,
    so a future change to either mapping cannot pass silently.
    """
    df = parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path))
    re_z = df["Re(Z) [Ω]"].to_numpy()
    im_z = -df["-Im(Z) [Ω]"].to_numpy()

    np.testing.assert_allclose(df["|Z| [Ω]"], np.hypot(re_z, im_z), rtol=_RTOL)
    np.testing.assert_allclose(df["θ [°]"], np.degrees(np.arctan2(im_z, re_z)), rtol=_RTOL)


def test_pstrace_log_columns_added(tmp_path):
    df = parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path))
    np.testing.assert_allclose(df["log(Frequency) [Hz]"], np.log10(df["Frequency [Hz]"]))
    np.testing.assert_allclose(df["log(|Z|) [Ω]"], np.log10(df["|Z| [Ω]"]))


def test_pstrace_rejects_non_pstrace_file(tmp_path):
    path = tmp_path / "not_eis.txt"
    path.write_text("alpha\tbeta\n1\t2\n")
    with pytest.raises(RuntimeError, match="valid PSTrace EIS export"):
        parse_pstrace_eis_txt(path)


@pytest.mark.xfail(
    reason=(
        "PSTrace's 'EIS data export settings' let the operator choose which columns are "
        "exported, so a valid export may carry only the three columns the EIS block "
        "actually needs. The parser currently requires all ten."
    ),
    strict=True,
)
def test_pstrace_accepts_minimal_column_selection(tmp_path):
    path = _make_pstrace_txt(tmp_path, columns=["Frequency", "Zdash", "Zdashneg"])
    df = parse_pstrace_eis_txt(path)
    assert {"Frequency [Hz]", "Re(Z) [Ω]", "-Im(Z) [Ω]"}.issubset(df.columns)


# --- Ivium --------------------------------------------------------------------


def test_ivium_negates_imaginary_part(tmp_path):
    """The one thing in this parser that breaks quietly if anyone touches it."""
    _, z = _spectrum()
    df = parse_ivium_eis_txt(_make_ivium_txt(tmp_path))
    np.testing.assert_allclose(df["-Im(Z) [Ω]"], -z.imag, rtol=_RTOL)
    # A capacitive cell must land in the upper half of the Nyquist plane
    assert (df["-Im(Z) [Ω]"] > 0).all()


def test_ivium_derives_magnitude_and_phase(tmp_path):
    _, z = _spectrum()
    df = parse_ivium_eis_txt(_make_ivium_txt(tmp_path))
    np.testing.assert_allclose(df["|Z| [Ω]"], np.abs(z), rtol=_RTOL)
    np.testing.assert_allclose(df["θ [°]"], np.degrees(np.angle(z)), rtol=_RTOL)


def test_ivium_rejects_non_ivium_file(tmp_path):
    path = tmp_path / "not_eis.txt"
    path.write_text("alpha\tbeta\n1\t2\n")
    with pytest.raises(RuntimeError, match="valid Ivium EIS export"):
        parse_ivium_eis_txt(path)


def test_ivium_no_header_variant(tmp_path):
    frequency, z = _spectrum()
    df = parse_ivium_eis_txt_no_header(_make_ivium_txt_no_header(tmp_path))
    np.testing.assert_allclose(df["Frequency [Hz]"], frequency, rtol=_RTOL)
    np.testing.assert_allclose(df["-Im(Z) [Ω]"], -z.imag, rtol=_RTOL)


def test_ivium_no_header_rejects_headed_file(tmp_path):
    """A file with column names must not be read as headerless data."""
    with pytest.raises(RuntimeError, match="headerless Ivium EIS export"):
        parse_ivium_eis_txt_no_header(_make_ivium_txt(tmp_path))


def test_ivium_no_header_rejects_two_columns(tmp_path):
    path = tmp_path / "two_col.txt"
    path.write_text("1.0\t2.0\n3.0\t4.0\n")
    with pytest.raises(RuntimeError, match="headerless Ivium EIS export"):
        parse_ivium_eis_txt_no_header(path)


# --- Cross-parser agreement ---------------------------------------------------


def test_pstrace_and_ivium_agree_on_the_same_spectrum(tmp_path):
    """One cell, two vendor layouts, one answer.

    This is the check that cannot be written with real data, because it would
    need the same cell measured on both instruments. It catches a sign or
    mapping error in either parser, including a disagreement between PSTrace's
    own ``Phase`` column and the phase datalab computes for Ivium.
    """
    pstrace = parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path))
    ivium = parse_ivium_eis_txt(_make_ivium_txt(tmp_path))

    for column in ("Frequency [Hz]", "Re(Z) [Ω]", "-Im(Z) [Ω]", "|Z| [Ω]", "θ [°]"):
        np.testing.assert_allclose(
            pstrace[column], ivium[column], rtol=_RTOL, err_msg=f"parsers disagree on {column}"
        )


def test_all_parsers_satisfy_the_block_requirements(tmp_path):
    """Every text parser must supply the three numeric columns EISBlock plots."""
    required = {"Re(Z) [Ω]", "-Im(Z) [Ω]", "Frequency [Hz]"}
    frames = (
        parse_pstrace_eis_txt(_make_pstrace_txt(tmp_path)),
        parse_ivium_eis_txt(_make_ivium_txt(tmp_path)),
        parse_ivium_eis_txt_no_header(_make_ivium_txt_no_header(tmp_path)),
    )
    for df in frames:
        assert required.issubset(set(df.select_dtypes("number").columns))
        assert len(df) > 0


# --- add_derived_eis_columns --------------------------------------------------


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
