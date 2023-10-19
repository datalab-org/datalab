import os
from typing import List, Tuple

import bokeh
import numpy as np
import pandas as pd
from pybaselines import Baseline
from rsciio.renishaw import file_reader
from scipy.signal import medfilt

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import mytheme, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id


class RamanBlock(DataBlock):
    blocktype = "raman"
    description = "Raman spectroscopy"
    accepted_file_extensions = (".txt",".wdf")

    @property
    def plot_functions(self):
        return (self.generate_raman_plot,)

    @classmethod
    def load_raman_spectrum(self, location: str, ext : str) -> Tuple[pd.DataFrame, List[str]]:
        if not isinstance(location, str):
            location = str(location)
        print(location)
        if ext == '.txt':
            df = pd.read_csv(location, sep=r"\s+")
            df = df.rename(columns={"#Wave": "wavenumber", "#Intensity": "intensity"})
        if ext == '.wdf':
            if self.test_1D_2D(location) == '1D':
                df = self.make_wdf_df(location)
            elif self.test_1D_2D(location) == '2D':
                raise RuntimeError('This is 2D Raman mapping data')
            else:
                raise RuntimeError('Unrecognised .wdf file')

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
        half_window = 30
        baseline_fitter = Baseline(x_data=df["wavenumber"])
        morphological_baseline = baseline_fitter.mor(
            df["normalized intensity"], half_window=half_window
        )[0]
        df["intensity - morphological baseline"] = (
            df["normalized intensity"] - morphological_baseline
        )
        df[
            f"baseline (`pybaselines.Baseline.mor`, {half_window=})"
        ] = morphological_baseline / np.max(df["intensity - morphological baseline"])
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

        return df, y_options
    
    @classmethod
    def test_1D_2D(self, location):
        raman_data = file_reader(location)
        if len(raman_data[0]['axes']) == 1:
            return '1D'
        elif len(raman_data[0]['axes']) == 3:
            return '2D'
        else:
            raise ValueError('Data is not compatible 1D or 2D Raman data')
    
    @classmethod
    def make_wdf_df(self, location):
        raman_data = file_reader(location)
        intensity = raman_data[0]['data']
        wavenumber_size = raman_data[0]['axes'][0]['size']
        wavenumber_offset = raman_data[0]['axes'][0]['offset']
        wavenumber_scale = raman_data[0]['axes'][0]['scale']
        wavenumbers = np.array([wavenumber_offset + i * wavenumber_scale for i in range(wavenumber_size)])
        df = pd.DataFrame({'wavenumber': wavenumbers, 'intensity': intensity})
        return df

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
        # if I don't pass ext here and try generate it in the function it doesn't recognise data attribute
            pattern_dfs, y_options = self.load_raman_spectrum(
                file_info["location"],
                ext 
            )
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

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)
