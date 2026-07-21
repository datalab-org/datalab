import warnings
from pathlib import Path
from typing import Any

import bokeh
import numpy as np
import pandas as pd
from scipy.signal import medfilt

from pydatalab.blocks.base import generate_js_callback_single_float_parameter
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot

from ...logger import LOGGER
from ...pipeline_block import PipelineDataBlock
from ...pipeline_block.block_stages import EventStage, ParserStage, PlotterStage, ProcessorStage
from .models import PeakInformation
from .utils import (
    compute_cif_pxrd_from_structure,
    parse_bruker_brml,
    parse_bruker_raw,
    parse_cif_pxrd,
    parse_rasx_zip,
    parse_xrdml,
)

_accepted_file_extensions = (".xrdml", ".xy", ".dat", ".xye", ".rasx", ".cif", ".raw", ".brml")


def set_wavelength(data, wavelength):
    LOGGER.info("Setting wavelength to %s", wavelength)
    if isinstance(wavelength, str):
        try:
            wavelength = float(wavelength)
        except Exception:
            raise ValueError(f"Invalid value for wavelength: {wavelength}. Must be a float.")

    if wavelength is None:
        wavelength = data["wavelength"]
    elif wavelength <= 0:
        raise ValueError("Wavelength must be a positive number")

    data["wavelength"] = wavelength


# File reading functions
def brute_csv_parse(location: "Path | str") -> "pd.DataFrame":
    columns = ["twotheta", "intensity", "error"]

    def _try_read_csv(sep: str, skiprows: int) -> pd.DataFrame | None:
        try:
            df = pd.read_csv(location, sep=sep, skiprows=skiprows, dtype=np.float64, names=columns)
            if df.empty:
                return None

            return df

        except (ValueError, RuntimeError):
            return None

    possible_separators = (r"\s+", ",")
    df = pd.DataFrame()
    # Try to parse the file by incrementing skiprows until all lines can be cast to np.float64
    # Set arbitrary limit to avoid infinite loop; a header of >1,000 lines is unlikely to be useful
    max_skiprows: int = 1_000
    final_skiprows: int = 0
    for skiprows in range(max_skiprows):
        for sep in possible_separators:
            df = _try_read_csv(sep, skiprows)
            if df is not None and not df.empty:
                final_skiprows = skiprows
                break

        if df is not None and not df.empty:
            final_skiprows = skiprows
            break

    # If no valid separator/skiprows combo was found, raise an error
    else:
        raise RuntimeError(
            f"Unable to extract XRD data from file {location}; check file header for irregularities"
        )

    if final_skiprows > 0:
        with open(location) as f:
            header = "".join([next(f) for _ in range(skiprows)])
            df.attrs["header"] = header
    return df


def compute_cif_structure(dfs: "list[pd.DataFrame]", wavelength: float) -> "list[pd.DataFrame]":
    new_dfs: list[pd.DataFrame] = []
    for df in dfs:
        if df.attrs.get("cif_structure", False):
            new_df, peak_data = compute_cif_pxrd_from_structure(df=df, wavelength=wavelength)
            # Track whether this is a computed PXRD that does not need background subtraction
            new_df.attrs = df.attrs | new_df.attrs
            new_df.attrs["theoretical"] = True
            new_df.attrs["peak_data"] = peak_data
            df = new_df
        new_dfs.append(df)
    return new_dfs


def read_raw_file(location: "str") -> pd.DataFrame:
    df, metadata = parse_bruker_raw(location)
    if wavelength := metadata.get("wavelength", None):
        df.attrs["wavelength"] = wavelength
    return df


# Process functions
def _calc_baselines_and_normalize(
    two_thetas,
    intensity,
    polyfit_deg: int = 15,
    kernel_size: int = 101,
    theoretical: bool = False,
):
    df = pd.DataFrame()

    df["sqrt(intensity)"] = np.sqrt(intensity)
    df["log(intensity)"] = np.log10(intensity)
    df["normalized intensity"] = intensity / np.max(intensity)

    if not theoretical:
        polyfit_baseline = np.poly1d(
            np.polyfit(two_thetas, df["normalized intensity"], deg=polyfit_deg)
        )(two_thetas)
        df["intensity - polyfit baseline"] = df["normalized intensity"] - polyfit_baseline
        df["intensity - polyfit baseline"] /= np.max(df["intensity - polyfit baseline"])
        df[f"baseline (`numpy.polyfit`, deg={polyfit_deg})"] = polyfit_baseline / np.max(
            df["intensity - polyfit baseline"]
        )
        median_baseline = medfilt(df["normalized intensity"], kernel_size=kernel_size)
        df["intensity - median baseline"] = df["normalized intensity"] - median_baseline
        df["intensity - median baseline"] /= np.max(df["intensity - median baseline"])
        df[f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})"] = (
            median_baseline / np.max(df["intensity - median baseline"])
        )
    else:
        df["intensity - polyfit baseline"] = df["normalized intensity"]
        df[f"baseline (`numpy.polyfit`, deg={polyfit_deg})"] = (
            0.0 * df["intensity - polyfit baseline"]
        )
        df["intensity - median baseline"] = df["normalized intensity"]
        df[f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})"] = (
            0 * df["intensity - median baseline"]
        )

    df["normalized intensity (staggered)"] = df["normalized intensity"]

    return df


def process_baseline_corrections(dfs: list[pd.DataFrame], wavelength) -> list[pd.DataFrame]:
    result_dfs = []
    peak_information = {}
    for ind, df in enumerate(dfs):
        df = df.rename(columns={"twotheta": "2θ (°)"})

        # if no wavelength (or invalid wavelength) is passed, don't convert to Q and d
        df_wavelength = df.attrs.get("wavelength", wavelength)
        if df_wavelength:
            try:
                df["Q (Å⁻¹)"] = 4 * np.pi / df_wavelength * np.sin(np.deg2rad(df["2θ (°)"]) / 2)
                df["d (Å)"] = 2 * np.pi / df["Q (Å⁻¹)"]
            except (ValueError, ZeroDivisionError):
                pass

        # Run baseline corrections but suppress numerical warnings around division by zero, sqrts and logs
        with warnings.catch_warnings():
            warnings_to_ignore = [
                (np.RankWarning, ".*Polyfit may be poorly conditioned*"),
                (RuntimeWarning, ".*invalid value encountered in sqrt*"),
                (UserWarning, ".*kernel_size exceeds volume extent*"),
                (RuntimeWarning, ".*divide by zero encountered in sqrt*"),
                (RuntimeWarning, ".*divide by zero encountered in log10*"),
                (RuntimeWarning, ".*invalid value encountered in log10*"),
                (RuntimeWarning, ".*divide by zero encountered in true_divide*"),
            ]
            for warning_type, message in warnings_to_ignore:
                warnings.filterwarnings("ignore", category=warning_type, message=message)

            y_option_df = _calc_baselines_and_normalize(
                df["2θ (°)"], df["intensity"], theoretical=df.attrs.get("theoretical", False)
            )
        attributes = df.attrs
        df = pd.concat([df, y_option_df], axis=1)
        df.attrs = attributes
        df.index.name = df.attrs.get("original_filename", "unknown") + (
            " (theoretical)" if df.attrs.get("theoretical", False) else ""
        )
        df.attrs["y_options"] = ["intensity"] + list(y_option_df.columns)
        peak_data = df.attrs.get("peak_data", {})
        peak_information[str(df.attrs["original_filename"])] = PeakInformation(
            **peak_data
        ).model_dump()
        df["normalized intensity (staggered)"] += ind

        result_dfs.append(df)

    # data["computed"] = {}
    # data["computed"]["peak_data"] = peak_information

    return result_dfs


def plotter(dfs: list[pd.DataFrame], wavelength: float, block_id: int) -> Any:
    plot = selectable_axes_plot(
        dfs,
        x_options=["2θ (°)", "Q (Å⁻¹)", "d (Å)"],
        y_default="normalized intensity (staggered)" if len(dfs) > 1 else "normalized intensity",
        y_options=dfs[0].attrs["y_options"],
        plot_line=True,
        plot_points=True,
        point_size=3,
        parameters={
            "wavelength": {
                "label": "Wavelength (Å)",
                "value": wavelength,
                "event": generate_js_callback_single_float_parameter(
                    "set_wavelength", "wavelength", str(block_id), throttled=False
                ),
            }
        },
    )
    return bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)


XRDBlock = PipelineDataBlock.define(
    "XRDBlock",
    blocktype="xrd",
    name="Powder XRD",
    description="Visualise XRD patterns and perform simple baseline corrections.",
    accepted_file_extensions=_accepted_file_extensions,
    defaults={"wavelength": 1.54060},
    events={"set_wavelength": EventStage(set_wavelength)},
    parser=[
        ParserStage(parse_xrdml, ".xrdml"),
        ParserStage(parse_rasx_zip, ".rasx"),
        ParserStage(parse_bruker_brml, ".brml"),
        ParserStage(parse_cif_pxrd, ".cif"),
        ParserStage(read_raw_file, ".raw"),
        ParserStage(brute_csv_parse, "*"),
    ],
    processor=[
        [ProcessorStage(compute_cif_structure, list_df_input=True)],
        [ProcessorStage(process_baseline_corrections, list_df_input=True)],
    ],
    plotter=PlotterStage(plotter, list_df_input=True),
    multi_file=True,
)
