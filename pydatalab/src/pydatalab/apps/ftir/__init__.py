import os
from pathlib import Path

import bokeh.embed
import numpy as np
import pandas as pd
from bokeh.models import HoverTool, LogColorMapper

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


def parse_ftir_asp(filename: Path):
    ftir = pd.read_csv(filename, header=None)
    number_of_points = int(ftir[0].iloc[0])
    start_wavenumber = ftir[0].iloc[1]
    end_wavenumber = ftir[0].iloc[2]
    x_range = np.linspace(start_wavenumber, end_wavenumber, number_of_points)
    y = ftir[0].iloc[-number_of_points:]
    ftir = pd.DataFrame.from_dict({"Wavenumber": x_range, "Absorbance": y})
    return ftir


class FTIRBlock(DataBlock):
    accepted_file_extensions = (".asp",)
    blocktype = "ftir"
    name = "FTIR"
    description = "This block can plot FTIR data from .asp files"

    @property
    def plot_functions(self):
        return (self.generate_ftir_plot,)

    def generate_ftir_plot(self):
        file_info = None
        # all_files = None
        ftir_data = None

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

            ftir_data = parse_ftir_asp(Path(file_info["location"]))

        if ftir_data is not None:
            layout = selectable_axes_plot(
                ftir_data,
                x_options=["Wavenumber"],
                y_options=["Absorbance"],
                x_range=(ftir_data["Wavenumber"].max() + 50, ftir_data["Wavenumber"].min() - 50),
                # color_options=["Frequency [Hz]"],
                color_mapper=LogColorMapper("Cividis256"),
                plot_points=False,
                plot_line=True,
                tools=HoverTool(
                    tooltips=[
                        ("Wavenumber / cm\u207b\u00b9", "@Wavenumber{0.00}"),
                        ("Absorbance", "@Absorbance{0.0000}"),
                    ],  # Display x and y values to specified decimal places
                    mode="vline",  # Ensures hover follows the x-axis
                ),
            )
            # Adding cm^-1 to the x-axis label using unicode characters - might be a more logical way
            layout.children[1].xaxis.axis_label = "Wavenumber / cm\u207b\u00b9"

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
