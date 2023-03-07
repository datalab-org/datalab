import os
from pathlib import Path

import bokeh

from pydatalab.apps.tga import parse
from pydatalab.blocks import DataBlock
from pydatalab.bokeh_plots import mytheme, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class TGABlock(DataBlock):
    blocktype = "tga"
    description = "Thermogravimetric analysis (TGA)"
    accepted_file_extensions = (".asc",)

    @property
    def plot_functions(self):
        return (self.generate_tga_plot,)

    def generate_tga_plot(self):
        file_info = None
        # all_files = None
        tga_data = None

        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
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

            tga_data = parse(Path(file_info["location"]))

        x_options = ["Time Relative [s]"]
        y_options = ["Partial Pressure [mbar]"]

        if tga_data:
            p = selectable_axes_plot(
                tga_data["data"],
                x_options=x_options,
                y_options=y_options,
                plot_line=True,
                plot_points=False,
                y_axis_type="log",
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)
