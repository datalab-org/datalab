import os
from pathlib import Path
from typing import List, Tuple

import bokeh
from bokeh.layouts import gridplot
from scipy.signal import savgol_filter

from pydatalab.apps.tga.parsers import parse_mt_mass_spec_ascii
from pydatalab.blocks._legacy import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_GRID_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class MassSpecBlock(DataBlock):
    blocktype = "ms"
    description = "Mass spectrometry (MS)"
    accepted_file_extensions = (".asc",)

    @property
    def plot_functions(self):
        return (self.generate_ms_plot,)

    def generate_ms_plot(self):
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

        if ms_data:
            # collect the maximum value of the data key for each species for plot ordering
            max_vals: List[Tuple[str, float]] = []

            for species in ms_data["data"]:
                data_key = (
                    "Partial Pressure [mbar]"
                    if "Partial Pressure [mbar]" in ms_data["data"][species]
                    else "Ion Current [A]"
                )
                data = ms_data["data"][species][data_key].to_numpy()

                ms_data["data"][species][f"{data_key} (Savitzky-Golay)"] = savgol_filter(
                    data, len(data) // 10, 3
                )

                max_vals.append((species, ms_data["data"][species][data_key].max()))

            plots = []
            for ind, (species, _) in enumerate(sorted(max_vals, key=lambda x: x[1], reverse=True)):
                plots.append(
                    selectable_axes_plot(
                        {species: ms_data["data"][species]},
                        x_options=x_options,
                        y_options=[data_key],
                        y_default=[
                            f"{data_key} (Savitzky-Golay)",
                            f"{data_key}",
                        ],
                        label_x=(ind == 0),
                        label_y=(ind == 0),
                        plot_line=True,
                        plot_points=False,
                        plot_title=f"Channel name: {species}",
                        plot_index=ind,
                        aspect_ratio=1.5,
                    )
                )

                plots[-1].children[0].xaxis[0].ticker.desired_num_ticks = 2

            # construct MxN grid of all species
            M = 3
            grid = []
            for i in range(0, len(plots), M):
                grid.append(plots[i : i + M])
            p = gridplot(grid, sizing_mode="scale_width", toolbar_location="below")

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_GRID_THEME)
