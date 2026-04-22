from pathlib import Path

import numpy as np
import pandas as pd
from galvani import MPRfile


def parse_ivium_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    column_map = {
        "Z1 /ohm": "Re(Z) [Ω]",
        "Z2 /ohm": "-Im(Z) [Ω]",
        "freq. /Hz": "Frequency [Hz]",
    }

    if not all(k in eis.columns for k in column_map):
        raise RuntimeError(
            f"File does not appear to be a valid Ivium EIS export, expected columns {column_map.keys()}, found {eis.columns}"
        )

    eis["Z2 /ohm"] *= -1
    eis.rename(
        column_map,
        inplace=True,
        axis="columns",
    )
    return eis


def parse_pstrace_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    column_map = {
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

    if not all(k in eis.columns for k in column_map):
        raise RuntimeError(
            f"File does not appear to be a valid PSTrace EIS export, expected columns {column_map.keys()}, found {eis.columns}"
        )

    eis.rename(
        column_map,
        inplace=True,
        axis="columns",
    )
    return eis


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


def parse_biologic_mpr(filename: Path):
    mpr_file = MPRfile(str(filename))
    df = pd.DataFrame(data=mpr_file.data)
    cols = {k: v for k, v in _BIOLOGIC_MPR_COLUMN_MAP.items() if k in df.columns}
    df = df[list(cols.keys())].rename(columns=cols)
    if "Frequency [Hz]" in df.columns:
        df["log(Frequency) [Hz]"] = np.log10(df["Frequency [Hz]"])
    if "|Z| [Ω]" in df.columns:
        df["log(|Z|) [Ω]"] = np.log10(df["|Z| [Ω]"])
    return df
