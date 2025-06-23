import os
import warnings
from pathlib import Path

import bokeh
import numpy as np
import pandas as pd
from scipy.signal import medfilt

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo

from .models import PeakInformation
from .utils import compute_cif_pxrd, parse_rasx_zip, parse_xrdml


class XRDBlock(DataBlock):
    blocktype = "xrd"
    name = "Powder XRD"
    description = "Visualize XRD patterns and perform simple baseline corrections."
    accepted_file_extensions = (".xrdml", ".xy", ".dat", ".xye", ".rasx", ".cif")

    defaults = {"wavelength": 1.54060}

    @property
    def plot_functions(self):
        return (self.generate_xrd_plot,)

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
            theoretical = True  # Track whether this is a computed PXRD that does not need background subtraction

        else:
            columns = ["twotheta", "intensity", "error"]
            possible_separators = (r"\s+", ",")
            df = pd.DataFrame()
            for sep in possible_separators:
                # Try to parse the file by incrementing skiprows until all lines can be cast to np.float64
                skiprows: int = 0
                # Set arbitrary limit to avoid infinite loop; a header of 10,000 lines is unlikely to be useful
                while skiprows < 1_000:
                    LOGGER.debug(
                        "Trying to read %s with skiprows=%d, sep=%s",
                        location.split("/")[-1],
                        skiprows,
                        sep,
                    )
                    try:
                        df = pd.read_csv(
                            location, sep=sep, names=columns, dtype=np.float64, skiprows=skiprows
                        )
                        break
                    except (ValueError, RuntimeError):
                        skiprows += 1

                if df.empty:
                    continue

                break

            # If no valid separator was found, raise an error
            else:
                raise RuntimeError(
                    f"Unable to extract XRD data from file {location}; check file header for irregularities"
                )

            if skiprows > 0:
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

    def generate_xrd_plot(self) -> None:
        """Generate a Bokeh plot potentially containing multiple XRD patterns.

        This function will first check whether a `file_id` is set in the block data.
        If not, it will interpret this as the "all compatible files" option, and will
        look into the item data to find all attached files, and attempt to read them as
        XRD patterns.

        Otherwise, the `file_id` will be used to load a single file.

        """
        file_info = None
        all_files = None
        pattern_dfs = None

        if self.data.get("file_id") is None:
            # If no file set, try to plot them all
            item_info = flask_mongo.db.items.find_one(
                {"item_id": self.data["item_id"]},
                projection={"file_ObjectIds": 1},
            )

            all_files = []
            for f in item_info["file_ObjectIds"]:
                try:
                    file_info = get_file_info_by_id(f, update_if_live=False)
                except OSError:
                    LOGGER.warning("Missing file found in database but no on disk: %s", f)
                    continue
                ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
                if any(
                    file_info["name"].lower().endswith(ext) for ext in self.accepted_file_extensions
                ):
                    all_files.append(file_info)

            if item_info["file_ObjectIds"] and not all_files:
                warnings.warn("No compatible files found in item")
                return None

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
                except Exception as exc:
                    warnings.warn(f"Could not parse file {f['location']} as XRD data. Error: {exc}")
                    continue
                peak_information[str(f["immutable_id"])] = PeakInformation(**peak_data).dict()
                pattern_df["normalized intensity (staggered)"] += ind
                pattern_dfs.append(pattern_df)

            self.data["peak_data"] = peak_information

        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                raise RuntimeError(
                    "XRDBlock.generate_xrd_plot(): Unsupported file extension (must be one of %s), not %s",
                    self.accepted_file_extensions,
                    ext,
                )

            pattern_dfs, y_options, peak_data = self.load_pattern(
                file_info["location"],
                wavelength=float(self.data.get("wavelength", self.defaults["wavelength"])),
            )
            peak_model = PeakInformation(**peak_data)
            if "peak_data" not in self.data:
                self.data["peak_data"] = {}
            self.data["peak_data"][str(file_info["immutable_id"])] = peak_model.dict()
            pattern_dfs = [pattern_dfs]

        if pattern_dfs:
            p = selectable_axes_plot(
                pattern_dfs,
                x_options=["2θ (°)", "Q (Å⁻¹)", "d (Å)"],
                y_default="normalized intensity",
                y_options=y_options,
                plot_line=True,
                plot_points=True,
                point_size=3,
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_THEME)
