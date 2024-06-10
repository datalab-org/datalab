import os
from pathlib import Path

import bokeh.embed

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .parsers import parse_tga_xlsx


class TgaDtaBlock(DataBlock):
    blocktype = "tga_dta"
    name = "TGA-DTA"
    description = "Read and visualize thermogravimetric analysis / differential thermal analysis data from Exstar SII Tg/DTA6300, and perform automated analysis"
    accepted_file_extensions = ".xlsx"

    @property
    def plot_functions(self):
        return (self.generate_tga_plot,)

    def generate_tga_plot(self):
        file_info = None

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

            df, metadata = parse_tga_xlsx(Path(file_info["location"]))

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
