import os
from pathlib import Path

import bokeh
import numpy as np
from bokeh.layouts import gridplot
from scipy.interpolate import splev, splrep

from pydatalab.apps.tga.parsers import parse_mt_mass_spec_ascii
from pydatalab.blocks.blocks import DataBlock
from pydatalab.bokeh_plots import selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class MassSpecBlock(DataBlock):
    blocktype = "ms"
    description = "Mass spectrometry (MS)"
    accepted_file_extensions = (".asc",)

    @property
    def plot_functions(self):
        return (self.generate_ms_plot,)

    def generate_ms_plot(self, grid_plot: bool = True):
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

            ms_data = parse_mt_mass_spec_ascii(Path(file_info["location"]))

        x_options = ["Time Relative [s]"]
        y_options = ["Partial Pressure [mbar]"]

        if ms_data:
            for species in ms_data["data"]:
                pressure = ms_data["data"][species]["Partial Pressure [mbar]"].to_numpy()
                time = ms_data["data"][species]["Time Relative [s]"].to_numpy()

                time = time[~np.isnan(time)]
                pressure = pressure[~np.isnan(pressure)]

                ms_data["data"][species]["Partial Pressure [mbar] (spline)"] = splev(
                    time,
                    splrep(
                        time,
                        pressure,
                        xe=time[~np.isnan(time)].max(),
                        xb=time[~np.isnan(time)].min(),
                        s=10,
                    ),
                )

            if grid_plot:
                plots = []
                for ind, species in enumerate(ms_data["data"]):
                    plots.append(
                        selectable_axes_plot(
                            {species: ms_data["data"][species]},
                            x_options=x_options,
                            y_options=y_options,
                            y_default=[
                                "Partial Pressure [mbar] (spline)",
                                "Partial Pressure [mbar]",
                            ],
                            plot_line=True,
                            plot_points=False,
                            plot_title=species,
                            plot_index=ind,
                        )
                    )
                # construct 3xN grid of all species
                grid = []
                for i in range(0, len(plots), 3):
                    grid.append(plots[i : i + 3])
                p = gridplot(grid, sizing_mode="scale_width", toolbar_location="below")
            else:
                p = selectable_axes_plot(
                    ms_data["data"],
                    x_options=x_options,
                    y_options=y_options,
                    plot_line=True,
                    plot_points=False,
                    y_axis_type="log",
                )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p)
