import os
import warnings
from pathlib import Path

import bokeh
import pandas as pd
from buba_utils.adsorb_analyze import AdsorbAnalyze
from buba_utils.pre_process import PreProcess

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_GRID_THEME
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .plot import buba_plot


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

    def plot_buba(self, sorbent_mass_g: float | None = None):
        file_info = None

        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return
        else:
            self.data["sorbent_mass_g"] = sorbent_mass_g
            if not sorbent_mass_g:
                warnings.warn("No sorbent mass provided; data will not be normalized.")
                sorbent_mass_g = 1.0

            # Assume instrment ID == #1 for now, implying BUBA
            self.data["instrument_id"] = 1

            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )
                return

            df = self.parse_buba(
                Path(file_info["location"]), instrument_id=self.data["instrument_id"]
            )

            # Calculate CO2 uptake
            analysis = AdsorbAnalyze(df)

            analysed = {}

            analysed["num_adsorb_trials"] = len(analysis.adsorb_trials)
            analysed["ads_capacity_co2"] = analysis.co2_uptake(sorbent_mass_g, single_point=True)
            analysed["trial_index"] = list(range(1, analysed["num_adsorb_trials"] + 1))
            uptakes = analysis.co2_uptake(sorbent_mass_g, single_point=False)
            analysed["co2_uptake_mmolco2_per_gsorbent"] = []
            for trial_index, _ in enumerate(analysed["trial_index"]):
                analysed["co2_uptake_mmolco2_per_gsorbent"].append(
                    uptakes[trial_index]["co2_uptake_mmolco2_per_gsorbent"]
                )

            time_column = "time_min" if "time_min" in df.columns else "time_s"

            for field in (
                "co2_in_ppm",
                "co2_out_ppm",
                "relative_humidity_in_percent",
                "relative_humidity_out_percent",
                time_column,
            ):
                analysed[field] = []
                for trial in analysis.adsorb_trials:
                    analysed[field].append(trial[field].tolist())

            if time_column == "time_min":
                analysed["time_s"] = [t * 60 for t in analysed["time_min"]]

            p = buba_plot(analysed, time_unit="min")
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_GRID_THEME)
