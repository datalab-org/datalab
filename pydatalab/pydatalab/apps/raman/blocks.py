import os
from typing import List, Tuple

import bokeh
import numpy as np
import pandas as pd
from scipy.signal import medfilt
from pybaselines import Baseline

from pydatalab.blocks.blocks import DataBlock
from pydatalab.bokeh_plots import mytheme, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo

# from .utils import parse_xrdml


class RamanBlock(DataBlock):
    blocktype = "raman"
    description = "Raman spectroscopy"
    accepted_file_extensions = (".txt")

    # don't think this is needed for Raman
    # potentially the laser wavelength used but don't think it matters
    # defaults = {"wavelength": 1.54060}

    @property
    def plot_functions(self):
        return (self.generate_raman_plot,)

    @classmethod
    def load_pattern(
        self, location: str
    ) -> Tuple[pd.DataFrame, List[str]]:

        if not isinstance(location, str):
            location = str(location)

        ext = os.path.splitext(location.split("/")[-1])[-1].lower()

        if ext == ".txt":
            df = pd.read_csv(location, sep=r"\s+")

        # elif ext == ".xy":
        #     df = pd.read_csv(location, sep=r"\s+", names=["twotheta", "intensity"])
        # leaving here for other file format e.g. .spc
        else:
            df = pd.read_csv(location, sep=r"\s+", names=["twotheta", "intensity", "error"])

        df = df.rename(columns={"#Wave": "Wavenumber", "#Intensity": "intensity"})

        # unnecessary for Raman
        # if no wavelength (or invalid wavelength) is passed, don't convert to Q and d
        # if wavelength:
        #     try:
        #         df["Q (Å⁻¹)"] = 4 * np.pi / wavelength * np.sin(np.deg2rad(df["2θ (°)"]) / 2)
        #         df["d (Å)"] = 2 * np.pi / df["Q (Å⁻¹)"]
        #     except (ValueError, ZeroDivisionError):
        #         pass

        df["sqrt(intensity)"] = np.sqrt(df["intensity"])
        df["log(intensity)"] = np.log10(df["intensity"])
        df["normalized intensity"] = df["intensity"] / np.max(df["intensity"])
        polyfit_deg = 15
        polyfit_baseline = np.poly1d(
            np.polyfit(df["Wavenumber"], df["normalized intensity"], deg=polyfit_deg)
        )(df["Wavenumber"])
        df["intensity - polyfit baseline"] = df["normalized intensity"] - polyfit_baseline
        df["intensity - polyfit baseline"] /= np.max(df["intensity - polyfit baseline"])
        df[f"baseline (`numpy.polyfit`, deg={polyfit_deg})"] = polyfit_baseline / np.max(
            df["intensity - polyfit baseline"]
        )

        kernel_size = 101
        median_baseline = medfilt(df["normalized intensity"], kernel_size=kernel_size)
        df["intensity - median baseline"] = df["normalized intensity"] - median_baseline
        df["intensity - median baseline"] /= np.max(df["intensity - median baseline"])
        df[
            f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})"
        ] = median_baseline / np.max(df["intensity - median baseline"])

        # baseline calculation I used in my data 
        half_window = 30
        baseline_fitter = Baseline(x_data = df["Wavenumber"])
        morphological_baseline = baseline_fitter.mor(df["normalized intensity"], half_window=half_window)[0]
        df["intensity - morphological baseline"] = df["normalized intensity"] - morphological_baseline
        df["intensity - morphological baseline"] /= np.max(df["intensity - morphological baseline"])
        df.index.name = location.split("/")[-1]

        y_options = [
            "normalized intensity",
            "intensity",
            "sqrt(intensity)",
            "log(intensity)",
            "intensity - median baseline",
            f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})",
            "intensity - polyfit baseline",
            f"baseline (`numpy.polyfit`, deg={polyfit_deg})",
            "intensity - morphological baseline",
            f"baseline (`pybaselines.Baseline.mor`, half_window={half_window})"
        ]

        return df, y_options

    def generate_raman_plot(self):
        file_info = None
        all_files = None
        pattern_dfs = None

        if "file_id" not in self.data:
            return None

        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                raise RuntimeError(
                    "RamanBlock.generate_raman_plot(): Unsupported file extension (must be one of %s), not %s",
                    self.accepted_file_extensions,
                    ext,
                )

            pattern_dfs, y_options = self.load_pattern(
                file_info["location"],
                # wavelength=float(self.data.get("wavelength", self.defaults["wavelength"])),
            )
            pattern_dfs = [pattern_dfs]

        if pattern_dfs:
            p = selectable_axes_plot(
                pattern_dfs,
                x_options=["Wavenumber"],
                y_options=y_options,
                plot_line=True,
                plot_points=True,
                point_size=3,
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)
