import os
from pathlib import Path

import bokeh
import numpy as np
import pandas as pd
from pybaselines import Baseline
from rsciio.renishaw import file_reader
from scipy.signal import medfilt

from pydatalab.blocks._legacy import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id


class RamanBlock(DataBlock):
    blocktype = "raman"
    description = "Raman spectroscopy"
    accepted_file_extensions = (".txt", ".wdf")

    @property
    def plot_functions(self):
        return (self.generate_raman_plot,)

    @classmethod
    def load(self, location: str | Path) -> tuple[pd.DataFrame, dict, list[str]]:
        if not isinstance(location, str):
            location = str(location)
        ext = os.path.splitext(location)[-1].lower()

        vendor = None
        metadata: dict = {}
        if ext == ".txt":
            try:
                header = []
                with open(location, encoding="cp1252") as f:
                    for line in f:
                        if line.startswith("#"):
                            header.append(line)
                    if "#Wave" in header[0] and "#Intensity" in header[0]:
                        vendor = "renishaw"
                    else:
                        metadata = {
                            key: value for key, value in [line.split("=") for line in header]
                        }
                        if (
                            metadata.get("#AxisType[0]") == "Intens\n"
                            and metadata.get("#AxisType[1]") == "Spectr\n"
                        ):
                            vendor = "labspec"
                if vendor == "renishaw":
                    df = pd.DataFrame(np.loadtxt(location), columns=["wavenumber", "intensity"])
                elif vendor == "labspec":
                    df = pd.DataFrame(
                        np.loadtxt(location, encoding="cp1252"), columns=["wavenumber", "intensity"]
                    )
                    metadata = {}
            except IndexError:
                pass
        elif ext == ".wdf":
            vendor = "renishaw"
            df, metadata = self.make_wdf_df(location)
        if not vendor:
            raise Exception(
                "Could not detect Raman data vendor -- this file type is not supported by this block."
            )

        df["sqrt(intensity)"] = np.sqrt(df["intensity"])
        df["log(intensity)"] = np.log10(df["intensity"])
        df["normalized intensity"] = df["intensity"] / np.max(df["intensity"])
        polyfit_deg = 15
        polyfit_baseline = np.poly1d(
            np.polyfit(df["wavenumber"], df["normalized intensity"], deg=polyfit_deg)
        )(df["wavenumber"])
        df["intensity - polyfit baseline"] = df["normalized intensity"] - polyfit_baseline
        df[f"baseline (`numpy.polyfit`, {polyfit_deg=})"] = polyfit_baseline / np.max(
            df["intensity - polyfit baseline"]
        )
        df["intensity - polyfit baseline"] /= np.max(df["intensity - polyfit baseline"])

        kernel_size = 101
        median_baseline = medfilt(df["normalized intensity"], kernel_size=kernel_size)
        df["intensity - median baseline"] = df["normalized intensity"] - median_baseline
        df[f"baseline (`scipy.signal.medfilt`, {kernel_size=})"] = median_baseline / np.max(
            df["intensity - median baseline"]
        )
        df["intensity - median baseline"] /= np.max(df["intensity - median baseline"])

        # baseline calculation I used in my data
        half_window = round(
            0.03 * df.shape[0]
        )  # a value which worked for my data, not sure how universally good it will be
        baseline_fitter = Baseline(x_data=df["wavenumber"])
        morphological_baseline = baseline_fitter.mor(
            df["normalized intensity"], half_window=half_window
        )[0]
        df["intensity - morphological baseline"] = (
            df["normalized intensity"] - morphological_baseline
        )
        df[f"baseline (`pybaselines.Baseline.mor`, {half_window=})"] = (
            morphological_baseline / np.max(df["intensity - morphological baseline"])
        )
        df["intensity - morphological baseline"] /= np.max(df["intensity - morphological baseline"])
        df.index.name = location.split("/")[-1]

        y_options = [
            "normalized intensity",
            "intensity",
            "sqrt(intensity)",
            "log(intensity)",
            "intensity - median baseline",
            f"baseline (`scipy.signal.medfilt`, {kernel_size=})",
            "intensity - polyfit baseline",
            f"baseline (`numpy.polyfit`, {polyfit_deg=})",
            "intensity - morphological baseline",
            f"baseline (`pybaselines.Baseline.mor`, {half_window=})",
        ]
        return df, metadata, y_options

    @classmethod
    def make_wdf_df(self, location: Path | str) -> pd.DataFrame:
        """Read the .wdf file with RosettaSciIO and try to extract
        1D Raman spectra.

        Parameters:
            location: The location of the file to read.

        Returns:
            A dataframe with the appropriate columns.

        """

        try:
            raman_data = file_reader(location)
        except Exception as e:
            raise RuntimeError(f"Could not read file with RosettaSciIO. Error: {e}")

        if len(raman_data[0]["axes"]) == 1:
            pass
        elif len(raman_data[0]["axes"]) == 3:
            raise RuntimeError("This block does not support 2D Raman yet.")
        else:
            raise RuntimeError("Data is not compatible 1D or 2D Raman data.")

        intensity = raman_data[0]["data"]
        wavenumber_size = raman_data[0]["axes"][0]["size"]
        wavenumber_offset = raman_data[0]["axes"][0]["offset"]
        wavenumber_scale = raman_data[0]["axes"][0]["scale"]
        wavenumbers = np.array(
            [wavenumber_offset + i * wavenumber_scale for i in range(wavenumber_size)]
        )
        df = pd.DataFrame({"wavenumber": wavenumbers, "intensity": intensity})
        return df, raman_data[0]["metadata"]

    def generate_raman_plot(self):
        file_info = None
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
            pattern_dfs, _, y_options = self.load(file_info["location"])
            pattern_dfs = [pattern_dfs]

        if pattern_dfs:
            p = selectable_axes_plot(
                pattern_dfs,
                x_options=["wavenumber"],
                y_options=y_options,
                plot_line=True,
                plot_points=True,
                point_size=3,
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_THEME)
