import os
import warnings
from pathlib import Path

import bokeh
import numpy as np
import pandas as pd
from scipy.signal import medfilt

from pydatalab.blocks.base import DataBlock, event, generate_js_callback_single_float_parameter
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .models import PeakInformation
from .utils import (
    compute_cif_pxrd,
    parse_bruker_brml,
    parse_bruker_raw,
    parse_rasx_zip,
    parse_xrdml,
)


class XRDBlock(DataBlock):
    blocktype = "xrd"
    name = "Powder XRD"
    description = "Visualize XRD patterns and perform simple baseline corrections."
    accepted_file_extensions = (".xrdml", ".xy", ".dat", ".xye", ".rasx", ".cif", ".raw", ".brml")
    multi_file = True

    defaults = {"wavelength": 1.54060}

    @property
    def plot_functions(self):
        return (self.generate_xrd_plot,)

    @event()
    def set_wavelength(self, wavelength: float | str | None):
        if isinstance(wavelength, str):
            try:
                wavelength = float(wavelength)
            except Exception:
                raise ValueError(f"Invalid value for wavelength: {wavelength}. Must be a float.")

        if wavelength is None:
            wavelength = self.defaults["wavelength"]
        elif wavelength <= 0:
            raise ValueError("Wavelength must be a positive number")

        self.data["wavelength"] = wavelength

    @classmethod
    def load_pattern(
        cls, location: str | Path, wavelength: float | None = None
    ) -> tuple[pd.DataFrame, list[str], dict]:
        """Load the XRD pattern at the given file location, returning
        a DataFrame with the pattern data, a list of y-axis options for plotting
        and a dictionary of peak metadata, if present.

        Parameters:
            location: The file location of the XRD pattern.
            wavelength: The wavelength of the X-ray source. Defaults to CuKa.

        """

        if not isinstance(location, str):
            location = str(location)

        ext = os.path.splitext(location.split("/")[-1])[-1].lower()

        theoretical = False
        peak_data: dict = {}

        if ext == ".xrdml":
            df = parse_xrdml(location)
        elif ext == ".rasx":
            df = parse_rasx_zip(location)
        elif ext == ".cif":
            df, peak_data = compute_cif_pxrd(
                location, wavelength=wavelength or cls.defaults["wavelength"]
            )
            # Track whether this is a computed PXRD that does not need background subtraction
            theoretical = True

        elif ext == ".raw":
            df, metadata = parse_bruker_raw(location)
            wavelength = metadata.get("wavelength", wavelength)

        elif ext == ".brml":
            df = parse_bruker_brml(location)

        else:
            columns = ["twotheta", "intensity", "error"]

            def _try_read_csv(sep: str, skiprows: int) -> pd.DataFrame | None:
                try:
                    df = pd.read_csv(
                        location, sep=sep, skiprows=skiprows, dtype=np.float64, names=columns
                    )
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

        if len(df) == 0:
            raise RuntimeError(f"No compatible data found in {location}")

        df = df.rename(columns={"twotheta": "2θ (°)"})

        # if no wavelength (or invalid wavelength) is passed, don't convert to Q and d
        if wavelength:
            try:
                df["Q (Å⁻¹)"] = 4 * np.pi / wavelength * np.sin(np.deg2rad(df["2θ (°)"]) / 2)
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

            y_option_df = cls._calc_baselines_and_normalize(
                df["2θ (°)"], df["intensity"], theoretical=theoretical
            )

        y_options = ["intensity"] + list(y_option_df.columns)

        df = pd.concat([df, y_option_df], axis=1)
        df.index.name = location.split("/")[-1] + (" (theoretical)" if theoretical else "")

        return df, y_options, peak_data

    @classmethod
    def _calc_baselines_and_normalize(
        cls,
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

    def generate_xrd_plot(self, filenames: list[str | Path] | None = None) -> None:
        """Generate a Bokeh plot potentially containing multiple XRD patterns.

        If no `filenames` are passed directly, the files to plot are taken from
        the `file_ids` set in the block data, falling back to the legacy
        single `file_id` if present.

        """
        pattern_dfs: list[pd.DataFrame] = []
        all_files: list[dict] = []

        if not filenames:
            file_ids = self.data.get("file_ids") or []
            if not file_ids and self.data.get("file_id"):
                file_ids = [self.data.get("file_id")]

            for f in file_ids:
                try:
                    file_info = get_file_info_by_id(f, update_if_live=False)
                except OSError:
                    LOGGER.warning("Missing file found in database but no on disk: %s", f)
                    continue

                if any(
                    file_info["name"].lower().endswith(ext) for ext in self.accepted_file_extensions
                ):
                    all_files.append(file_info)

        else:
            if isinstance(filenames, (str, Path)):
                filenames = [filenames]

            all_files = [{"location": filename, "immutable_id": filename} for filename in filenames]

        pattern_dfs = []
        peak_information = {}
        y_options: list[str] = []
        for ind, f in enumerate(all_files):
            try:
                peak_data: dict = {}
                pattern_df, y_options, peak_data = self.load_pattern(
                    f["location"],
                    wavelength=float(self.data.get("wavelength", self.defaults["wavelength"])),
                )
                pattern_df.attrs["item_id"] = self.data.get("item_id", "unknown")
                pattern_df.attrs["original_filename"] = f.get("name", "unknown")
                pattern_df.attrs["wavelength"] = (
                    f"{self.data.get('wavelength', self.defaults['wavelength'])} Å"
                )
            except Exception as exc:
                warnings.warn(f"Could not parse file {f['location']} as XRD data. Error: {exc}")
                continue
            peak_information[str(f["immutable_id"])] = PeakInformation(**peak_data).dict()
            if len(all_files) > 1:
                pattern_df["normalized intensity (staggered)"] += ind
            pattern_dfs.append(pattern_df)

        self.data["computed"] = {}
        self.data["computed"]["peak_data"] = peak_information

        if pattern_dfs:
            p = self._make_plots(pattern_dfs, y_options)
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_THEME)

    def _make_plots(self, pattern_dfs: list[pd.DataFrame], y_options: list[str]):
        return selectable_axes_plot(
            pattern_dfs,
            x_options=["2θ (°)", "Q (Å⁻¹)", "d (Å)"],
            y_default="normalized intensity (staggered)"
            if len(pattern_dfs) > 1
            else "normalized intensity",
            y_options=y_options,
            plot_line=True,
            plot_points=True,
            point_size=3,
            parameters={
                "wavelength": {
                    "label": "Wavelength (Å)",
                    "value": self.data["wavelength"],
                    "event": generate_js_callback_single_float_parameter(
                        "set_wavelength", "wavelength", self.block_id, throttled=False
                    ),
                }
            },
        )
