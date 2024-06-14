import os
from typing import List, Tuple

import bokeh
import numpy as np
import pandas as pd
from scipy.signal import medfilt

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo

from .utils import parse_xrdml


class XRDBlock(DataBlock):
    blocktype = "xrd"
    name = "Powder XRD"
    description = "Visualize XRD patterns and perform simple baseline corrections."
    accepted_file_extensions = (".xrdml", ".xy", ".dat", ".xye")

    defaults = {"wavelength": 1.54060}

    @property
    def plot_functions(self):
        return (self.generate_xrd_plot,)

    @classmethod
    def load_pattern(
        self, location: str, wavelength: float | None = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        if not isinstance(location, str):
            location = str(location)

        ext = os.path.splitext(location.split("/")[-1])[-1].lower()

        if ext == ".xrdml":
            df = parse_xrdml(location)

        elif ext == ".xy":
            df = pd.read_csv(location, sep=r"\s+", names=["twotheta", "intensity"])

        else:
            df = pd.read_csv(location, sep=r"\s+", names=["twotheta", "intensity", "error"])

        df = df.rename(columns={"twotheta": "2θ (°)"})

        # if no wavelength (or invalid wavelength) is passed, don't convert to Q and d
        if wavelength:
            try:
                df["Q (Å⁻¹)"] = 4 * np.pi / wavelength * np.sin(np.deg2rad(df["2θ (°)"]) / 2)
                df["d (Å)"] = 2 * np.pi / df["Q (Å⁻¹)"]
            except (ValueError, ZeroDivisionError):
                pass

        df["sqrt(intensity)"] = np.sqrt(df["intensity"])
        df["log(intensity)"] = np.log10(df["intensity"])
        df["normalized intensity"] = df["intensity"] / np.max(df["intensity"])
        polyfit_deg = 15
        polyfit_baseline = np.poly1d(
            np.polyfit(df["2θ (°)"], df["normalized intensity"], deg=polyfit_deg)
        )(df["2θ (°)"])
        df["intensity - polyfit baseline"] = df["normalized intensity"] - polyfit_baseline
        df["intensity - polyfit baseline"] /= np.max(df["intensity - polyfit baseline"])
        df[f"baseline (`numpy.polyfit`, deg={polyfit_deg})"] = polyfit_baseline / np.max(
            df["intensity - polyfit baseline"]
        )

        kernel_size = 101
        median_baseline = medfilt(df["normalized intensity"], kernel_size=kernel_size)
        df["intensity - median baseline"] = df["normalized intensity"] - median_baseline
        df["intensity - median baseline"] /= np.max(df["intensity - median baseline"])
        df[f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})"] = (
            median_baseline / np.max(df["intensity - median baseline"])
        )

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
        ]

        return df, y_options

    def generate_xrd_plot(self):
        file_info = None
        all_files = None
        pattern_dfs = None

        if "file_id" not in self.data:
            # If no file set, try to plot them all
            item_info = flask_mongo.db.items.find_one(
                {"item_id": self.data["item_id"]},
            )

            all_files = [
                d
                for d in [
                    get_file_info_by_id(f, update_if_live=False)
                    for f in item_info["file_ObjectIds"]
                ]
                if any(d["name"].lower().endswith(ext) for ext in self.accepted_file_extensions)
            ]

            if not all_files:
                LOGGER.warning("XRDBlock.generate_xrd_plot(): No files found on sample")
                return

            pattern_dfs = []
            for f in all_files:
                try:
                    pattern_df, y_options = self.load_pattern(
                        f["location"],
                        wavelength=float(self.data.get("wavelength", self.defaults["wavelength"])),
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"Could not parse file {file_info['location']}. Error: {exc}"
                    )
                pattern_dfs.append(pattern_df)

        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                raise RuntimeError(
                    "XRDBlock.generate_xrd_plot(): Unsupported file extension (must be one of %s), not %s",
                    self.accepted_file_extensions,
                    ext,
                )

            pattern_dfs, y_options = self.load_pattern(
                file_info["location"],
                wavelength=float(self.data.get("wavelength", self.defaults["wavelength"])),
            )
            pattern_dfs = [pattern_dfs]

        if pattern_dfs:
            p = selectable_axes_plot(
                pattern_dfs,
                x_options=["2θ (°)", "Q (Å⁻¹)", "d (Å)"],
                y_options=y_options,
                plot_line=True,
                plot_points=True,
                point_size=3,
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_THEME)
