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

    return (
        weight_change_temp_1percent,
        weight_change_temp_5percent,
        weight_change_temp_10percent,
    )

    # df["relative differential mass (%/min)"]

    # dtg_filt = medfilt(df["relative differential mass (%/min)"], kernal=5) # use a median filter to get rid of any spikes
    # dtg_1percent = np.nonzero(dtg_filt >= 1)[0][0]


class TgaDtaBlock(DataBlock):
    blocktype = "tga_dta"
    name = "TGA-DTA"
    description = "Read and visualize thermogravimetric analysis / differential thermal analysis data from Exstar SII Tg/DTA6300, and perform automated analysis"
    accepted_file_extensions = ".xlsx"

    data_model = TgaData
    metadata_model = TgaMetadata
    analysis_model = TgaAnalysis

    metadata: dict = {}
    analysis: dict = {}

    def _process_data(self, df):
        initial_mass = df["mass (μg)"].iloc[0]
        df["mass change (%)"] = (df["mass (μg)"] - initial_mass) / initial_mass * 100
        # df["relative differential mass (%/min)"] = df["differential mass (μg/min)"]/initial_mass*100

        nsteps = len(self.metadata.temperature_program.steps)
        step_boundaries = _split_df(df, nsteps)
        dfs = [df.iloc[start:end] for start, end in step_boundaries]

        (
            weight_change_temp_1percent,
            weight_change_temp_5percent,
            weight_change_temp_10percent,
        ) = _extract_oxidation_parameters(dfs[0])

        self.analysis = TgaAnalysis(
            **{
                "nsteps": nsteps,
                "step_boundaries": step_boundaries,
                "weight_change_temp_1percent": weight_change_temp_1percent,
                "weight_change_temp_5percent": weight_change_temp_5percent,
                "weight_change_temp_10percent": weight_change_temp_10percent,
            }
        )
        return df

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

        df = self._process_data(df)

        # x_options = [""]
        bokeh_layout = selectable_axes_plot(
            df,
            x_options=["temperature (°C)", "elapsed time (min)"],
            y_options=[
                "mass (μg)",
                "differential mass (μg/min)",
                "DTA voltage (μV)",
                "elapsed time (min)",
                "temperature (°C)",
            ],
            plot_line=True,
            point_size=3,
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(
            bokeh_layout, theme=DATALAB_BOKEH_THEME
        )
