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

_PALMSENS_PSSESSION_COLUMN_MAP = {
    "Frequency": "Frequency [Hz]",
    "ZRe": "Re(Z) [Ω]",
    "ZIm": "-Im(Z) [Ω]",
    "Z": "|Z| [Ω]",
    "Phase": "θ [°]",
    "potential": "Edc [V]",
    "Idc": "Idc [A]",
    "Y": "|Y| [S]",
    "YRe": "Re(Y) [S]",
    "YIm": "Im(Y) [S]",
    "Capacitance": "|C| [F]",
    "Capacitance'": "Re(C) [F]",
    "Capacitance''": "Im(C) [F]",
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


def parse_ivium_eis_txt_no_header(filename: Path):
    eis = pd.read_csv(
        filename, sep="\t", header=None, names=["Frequency [Hz]", "Re(Z) [Ω]", "-Im(Z) [Ω]"]
    )

    if len(eis.columns) != 3:
        raise RuntimeError(
            f"File does not appear to be a headerless Ivium EIS export, expected 3 columns, found {len(eis.columns)}"
        )

    if not all(pd.api.types.is_numeric_dtype(eis[c]) for c in eis.columns):
        raise RuntimeError(
            "File does not appear to be a headerless Ivium EIS export, expected all numeric columns"
        )

    if eis.isnull().any(axis=None):
        raise RuntimeError(
            "File does not appear to be a headerless Ivium EIS export, found null values (file may have fewer than 3 tab-separated columns)"
        )

    return add_derived_eis_columns(eis)


def parse_pstrace_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    if not all(k in eis.columns for k in _PSTRACE_COLUMN_MAP):
        raise RuntimeError(
            f"File does not appear to be a valid PSTrace EIS export, expected columns {_PSTRACE_COLUMN_MAP.keys()}, found {eis.columns}"
        )

    eis.rename(_PSTRACE_COLUMN_MAP, inplace=True, axis="columns")
    return add_derived_eis_columns(eis)


_BIOLOGIC_MPR_REQUIRED_COLUMNS = {"Frequency [Hz]", "Re(Z) [Ω]", "-Im(Z) [Ω]"}


def parse_biologic_mpr(filename: Path):
    try:
        mpr_file = MPRfile(str(filename))
        df = pd.DataFrame(data=mpr_file.data)
    except Exception as exc:
        raise RuntimeError(f"Failed to read Biologic .mpr file: {exc}") from exc
    cols = {k: v for k, v in _BIOLOGIC_MPR_COLUMN_MAP.items() if k in df.columns}
    df = df[list(cols.keys())].rename(columns=cols)
    missing = _BIOLOGIC_MPR_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError(
            f"File does not appear to be a valid Biologic EIS export, missing required columns: {missing}"
        )
    return add_derived_eis_columns(df)


def parse_palmsens_pssession(filename: Path):
    import json

    try:
        raw = filename.read_bytes().decode("utf-16")
        # PSTrace appends a UTF-16 BOM (U+FEFF) after the closing }, so slice to the last } exactly
        data = json.loads(raw[: raw.rfind("}") + 1])
        arrays = data["measurements"][0]["dataset"]["values"]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"File does not appear to be a valid PalmSens .pssession file: {exc}"
        ) from exc
    except (KeyError, IndexError) as exc:
        raise RuntimeError(
            f"File does not appear to be a valid PalmSens EIS session, unexpected structure: {exc}"
        ) from exc

    by_description = {a["description"]: a for a in arrays}

    required = {"Frequency", "ZRe", "ZIm"}
    if not required.issubset(by_description):
        raise RuntimeError(
            f"File does not appear to be a valid PalmSens EIS session, expected arrays {required}, found {set(by_description)}"
        )

    rows = {
        new_name: [pt["v"] for pt in by_description[old_name]["datavalues"]]
        for old_name, new_name in _PALMSENS_PSSESSION_COLUMN_MAP.items()
        if old_name in by_description
    }
    df = pd.DataFrame(rows)
    return add_derived_eis_columns(df)
