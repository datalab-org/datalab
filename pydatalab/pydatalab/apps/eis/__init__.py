import os
from pathlib import Path

import bokeh.embed
import pandas as pd
from bokeh.models import HoverTool, LogColorMapper

from pydatalab.blocks._legacy import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


def parse_ivium_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")
    eis["Z2 /ohm"] *= -1
    eis.rename(
        {"Z1 /ohm": "Re(Z) [Ω]", "Z2 /ohm": "-Im(Z) [Ω]", "freq. /Hz": "Frequency [Hz]"},
        inplace=True,
        axis="columns",
    )
    return eis


class EISBlock(DataBlock):
    accepted_file_extensions = [".txt"]
    blocktype = "eis"
    name = "Electrochemical Impedance Spectroscopy"
    description = "Electrochemical Impedance Spectroscopy"

    @property
    def plot_functions(self):
        return (self.generate_eis_plot,)

    def generate_eis_plot(self):
        file_info = None
        # all_files = None
        eis_data = None

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

            eis_data = parse_ivium_eis_txt(Path(file_info["location"]))

        if eis_data is not None:
            plot = selectable_axes_plot(
                eis_data,
                x_options=["Re(Z) [Ω]"],
                y_options=["-Im(Z) [Ω]"],
                color_options=["Frequency [Hz]"],
                color_mapper=LogColorMapper("Cividis256"),
                plot_points=True,
                plot_line=False,
                tools=HoverTool(tooltips=[("Frequency [Hz]", "@{Frequency [Hz]}")]),
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)
