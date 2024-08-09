import os
from pathlib import Path

import bokeh
import pandas as pd
from buba_utils.adsorb_analyze import AdsorbAnalyze
from buba_utils.pre_process import PreProcess

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_GRID_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class BubaBlock(DataBlock):
    blocktype = "buba"
    name = "Buba test rig"
    description = "Analyse data from the Buba test rig"
    accepted_file_extensions = (".csv",)

    @property
    def plot_functions(self):
        return (self.plot_buba,)

    @classmethod
    def parse_buba(cls, path: Path, instrument_id: int = 1) -> pd.DataFrame:
        return PreProcess(path, instrument_id).df

    def plot_buba(self):
        file_info = None
        trial = 1
        instrument_id = 1
        sorbent_mass = 0.0267

        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return
        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )
                return

            df = self.parse_buba(Path(file_info["location"]), instrument_id=instrument_id)
            analysis = AdsorbAnalyze(df)

            self.data["ads_capacity_co2"] = analysis.co2_uptake(sorbent_mass, single_point=True)

            # Calculate CO2 uptake
            ads_uptakes = analysis.co2_uptake(sorbent_mass, single_point=False)

            # Extract specific adsorption trial
            ads_uptake = ads_uptakes[trial]

            df["co2_in_ppm"] = analysis.adsorb_trials[trial]["co2_in_ppm"]
            df["co2_out_ppm"] = analysis.adsorb_trials[trial]["co2_out_ppm"]
            df["co2_uptake_mmolco2_per_gsorbent"] = ads_uptake["co2_uptake_mmolco2_per_gsorbent"]
            df["relative_humidity_in_percent"] = analysis.adsorb_trials[trial][
                "relative_humidity_in_percent"
            ]
            df["relative_humidity_out_percent"] = analysis.adsorb_trials[trial][
                "relative_humidity_out_percent"
            ]

            time_column = "time_min" if "time_min" in df.columns else "time_s"

            df[time_column] = analysis.adsorb_trials[trial][time_column]

            p = selectable_axes_plot(
                df,
                x_options=[time_column],
                y_options=[
                    "co2_out_ppm",
                    "co2_uptake_mmolco2_per_gsorbent",
                    "co2_in_ppm",
                    "relative_humidity_in_percent",
                    "relative_humidity_out_percent",
                ],
                plot_points=False,
                plot_line=True,
                # plot_title="CO₂ Breakthrough Curve",
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_GRID_THEME)
