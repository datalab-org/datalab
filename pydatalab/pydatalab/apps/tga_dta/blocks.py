import os
from pathlib import Path
from typing import List, Tuple

import bokeh.embed
import numpy as np
from scipy.signal import medfilt

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .models import TgaAnalysis, TgaData, TgaMetadata
from .parsers import parse_tga_xlsx


def _split_df(df, nsteps) -> List[Tuple[int, int]]:
    """currently, assumes there are only two steps (heating and cooling) in a run"""
    if nsteps == 1:
        return [(0, len(df))]
    if nsteps == 2:
        switch_idx = df["temperature (°C)"].idxmax()
        return [(0, switch_idx), (switch_idx, len(df))]

    else:
        raise ValueError("TGA_DTA block currently only supports datasets with 1 or 2 steps in them")


def _extract_oxidation_parameters(df):
    # use a median filter to get rid of any spikes
    mass_change_filt = medfilt(df["mass change (%)"], kernel_size=5)

    weight_change_temp_1percent = np.nonzero(mass_change_filt >= 1)[0][0]
    weight_change_temp_5percent = np.nonzero(mass_change_filt >= 5)[0][0]
    weight_change_temp_10percent = np.nonzero(mass_change_filt >= 10)[0][0]

    differential_weight_change = medfilt(df["relative differential mass (%/min)"], kernel_size=5)
    max_weight_change_idx = np.argmax(np.abs(differential_weight_change))
    max_weight_change_temp = df["temperature (°C)"].iloc[max_weight_change_idx]

    # check if the max weight change is near the boundary. If it is, then this is a sign that
    # there is no oxidation event in the data, and we potentially shouldn't report it.
    max_temp = df["temperature (°C)"].max()
    min_temp = df["temperature (°C)"].min()
    if (max_temp - max_weight_change_temp < 5) or (max_weight_change_temp - min_temp < 5):
        LOGGER.debug(
            "the max point of fastest weight change is close to the boundaries of the measurement, so no max weight change is recorded."
        )
        # max_weight_change_temp = None
        # max_weight_change_slope = None
        # max_weight_change_relweight = None
        # onset_temperature = None

    # calculate slope of %/°C (different from DTG, which is %/min!) for 5 points on either side of the max
    local_df = -df.iloc[max_weight_change_idx - 5 : max_weight_change_idx + 5]
    p = np.polyfit(local_df["temperature (°C)"], local_df["mass change (%)"], deg=1)
    max_weight_change_slope = p[0]

    max_weight_change_relweight = df["mass change (%)"].iloc[max_weight_change_idx]
    onset_temperature = (
        max_weight_change_temp - max_weight_change_relweight / max_weight_change_slope
    )

    return (
        weight_change_temp_1percent,
        weight_change_temp_5percent,
        weight_change_temp_10percent,
        max_weight_change_temp,
        max_weight_change_slope,
        max_weight_change_relweight,
        onset_temperature,
    )


class TgaDtaBlock(DataBlock):
    blocktype = "tga_dta"
    name = "TGA-DTA"
    description = "Read and visualize thermogravimetric analysis / differential thermal analysis data from Exstar SII Tg/DTA6300, and perform automated analysis"
    accepted_file_extensions = [".xlsx", ".xls"]

    data_model = TgaData
    metadata_model = TgaMetadata
    analysis_model = TgaAnalysis

    metadata: dict = {}
    analysis: dict = {}

    def _process_data(self, df):
        initial_mass = df["mass (μg)"].iloc[0]
        df["mass change (%)"] = (df["mass (μg)"] - initial_mass) / initial_mass * 100
        df["relative differential mass (%/min)"] = (
            df["differential mass (μg/min)"] / initial_mass * 100
        )

        nsteps = len(self.metadata.temperature_program.steps)
        step_boundaries = _split_df(df, nsteps)
        dfs = [df.iloc[start:end] for start, end in step_boundaries]

        (
            weight_change_temp_1percent,
            weight_change_temp_5percent,
            weight_change_temp_10percent,
            max_weight_change_temp,
            max_weight_change_slope,
            max_weight_change_relweight,
            onset_temperature,
        ) = _extract_oxidation_parameters(dfs[0])

        self.analysis = TgaAnalysis(
            **{
                "nsteps": nsteps,
                "step_boundaries": step_boundaries,
                "weight_change_temp_1percent": weight_change_temp_1percent,
                "weight_change_temp_5percent": weight_change_temp_5percent,
                "weight_change_temp_10percent": weight_change_temp_10percent,
                "max_weight_change_temp": max_weight_change_temp,
                "max_weight_change_slope": max_weight_change_slope,
                "max_weight_change_relweight": max_weight_change_relweight,
                "onset_temperature": onset_temperature,
            }
        )

    @property
    def plot_functions(self):
        return (self.generate_tga_plot,)

    def generate_tga_plot(self):
        file_info = None

        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
        if ext not in self.accepted_file_extensions:
            LOGGER.warning(
                "Unsupported file extension (must be one of %s, not %s)",
                self.accepted_file_extensions,
                ext,
            )
            return

        df, metadata = parse_tga_xlsx(Path(file_info["location"]))
        self.metadata = metadata

        self._process_data(df)

        if self.analysis.onset_temperature:
            df["tangent_line"] = (
                self.analysis.max_weight_change_slope
                * (df["temperature (°C)"] - self.analysis.max_weight_change_temp)
                + self.analysis.max_weight_change_relweight
            )
            df["tangent_line"] = df["tangent_line"].where(df["tangent_line"] > 0, np.nan)

        # x_options = [""]
        bokeh_layout = selectable_axes_plot(
            df,
            x_options=["temperature (°C)", "elapsed time (min)"],
            y_options=[
                "mass (μg)",
                "mass change (%)",
                "differential mass (μg/min)",
                "relative differential mass (%/min)",
                "DTA voltage (μV)",
                "elapsed time (min)",
                "temperature (°C)",
            ],
            x_default="temperature (°C)",
            y_default=[
                "mass change (%)",
                "relative differential mass (%/min)",
                "tangent_line",
            ],
            plot_line=True,
            point_size=3,
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(
            bokeh_layout, theme=DATALAB_BOKEH_THEME
        )
