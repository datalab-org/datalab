import os
from pathlib import Path
from typing import List, Tuple

import bokeh
from bokeh.layouts import gridplot
from scipy.signal import savgol_filter

from pydatalab.apps.tga.parsers import parse_mt_mass_spec_ascii
from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_GRID_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .parsers import parse_buba
from .analysis import AdsorbAnalyze


class BubaBlock(DataBlock):
    blocktype = "buba"
    name = "Buba test rig"
    description = "Analyse data from the Buba test rig"
    accepted_file_extensions = (".csv", )

    @property
    def plot_functions(self):
        return (self.plot_buba,)

    def plot_buba(self):
        file_info = None
        # all_files = None
        ms_data = None

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

            df = parse_buba(Path(file_info["location"]), instrument_id=1)
            analysis = AdsorbAnalyze(df)

            breakpoint()

            p = selectable_axes_plot(df)

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_GRID_THEME)
