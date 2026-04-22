from pathlib import Path

import numpy as np
import pandas as pd
from galvani import MPRfile

_IVIUM_COLUMN_MAP = {
    "Z1 /ohm": "Re(Z) [Ω]",
    "Z2 /ohm": "-Im(Z) [Ω]",
    "freq. /Hz": "Frequency [Hz]",
}

_PSTRACE_COLUMN_MAP = {
    "Frequency": "Frequency [Hz]",
    "Zdash": "Re(Z) [Ω]",
    "Zdashneg": "-Im(Z) [Ω]",
    "Z": "|Z| [Ω]",
    "Phase": "θ [°]",
    "Y": "|Y| [S]",
    "YRe": "Re(Y) [S]",
    "YIm": "Im(Y) [S]",
    "Cdash": "Re(C) [F]",
    "Cdashdash": "Im(C) [F]",
}

_BIOLOGIC_MPR_COLUMN_MAP = {
    "freq/Hz": "Frequency [Hz]",
    "Re(Z)/Ohm": "Re(Z) [Ω]",
    "-Im(Z)/Ohm": "-Im(Z) [Ω]",
    "|Z|/Ohm": "|Z| [Ω]",
    "Phase(Z)/deg": "θ [°]",
    "time/s": "Time [s]",
    "<Ewe>/V": "Ewe [V]",
    "<I>/mA": "I [mA]",
    "Cs/µF": "Cs [µF]",
    "Cp/µF": "Cp [µF]",
}


def add_derived_eis_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute |Z|, θ, and log columns from Re(Z) and -Im(Z) if not already present."""
    if "|Z| [Ω]" not in df.columns and {"Re(Z) [Ω]", "-Im(Z) [Ω]"}.issubset(df.columns):
        df["|Z| [Ω]"] = np.sqrt(df["Re(Z) [Ω]"] ** 2 + df["-Im(Z) [Ω]"] ** 2)
    if "θ [°]" not in df.columns and {"Re(Z) [Ω]", "-Im(Z) [Ω]"}.issubset(df.columns):
        df["θ [°]"] = np.degrees(np.arctan2(-df["-Im(Z) [Ω]"], df["Re(Z) [Ω]"]))
    if "Frequency [Hz]" in df.columns:
        df["log(Frequency) [Hz]"] = np.log10(df["Frequency [Hz]"])
    if "|Z| [Ω]" in df.columns:
        df["log(|Z|) [Ω]"] = np.log10(df["|Z| [Ω]"])
    return df


def parse_ivium_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    if not all(k in eis.columns for k in _IVIUM_COLUMN_MAP):
        raise RuntimeError(
            f"File does not appear to be a valid Ivium EIS export, expected columns {_IVIUM_COLUMN_MAP.keys()}, found {eis.columns}"
        )

    eis["Z2 /ohm"] *= -1
    eis.rename(_IVIUM_COLUMN_MAP, inplace=True, axis="columns")
    return add_derived_eis_columns(eis)


def parse_pstrace_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    if not all(k in eis.columns for k in _PSTRACE_COLUMN_MAP):
        raise RuntimeError(
            f"File does not appear to be a valid PSTrace EIS export, expected columns {_PSTRACE_COLUMN_MAP.keys()}, found {eis.columns}"
        )

    eis.rename(_PSTRACE_COLUMN_MAP, inplace=True, axis="columns")
    return add_derived_eis_columns(eis)


def parse_biologic_mpr(filename: Path):
    mpr_file = MPRfile(str(filename))
    df = pd.DataFrame(data=mpr_file.data)
    cols = {k: v for k, v in _BIOLOGIC_MPR_COLUMN_MAP.items() if k in df.columns}
    df = df[list(cols.keys())].rename(columns=cols)
    return add_derived_eis_columns(df)
