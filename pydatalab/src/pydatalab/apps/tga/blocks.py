import os
from pathlib import Path

import bokeh
import scipy
from bokeh.layouts import gridplot
from scipy.signal import savgol_filter

from pydatalab.apps.tga.parsers import parse_mt_mass_spec_ascii, parse_mt_mass_spec_txt
from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_GRID_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class MassSpecBlock(DataBlock):
    blocktype = "ms"
    name = "Mass spectrometry"
    description = "Read and visualize mass spectrometry data as a grid plot per channel"
    accepted_file_extensions = (".asc", ".txt")
    multi_file = True

    @property
    def plot_functions(self):
        return (self.generate_ms_plot,)

    def generate_ms_plot(self):
        """
        Generates MS plot from uploaded files
        - .asc: partial pressures data
        - .txt Differential Thermal Analysis data
        No other files are accepted.
        """
        if self.data.get("file_ids", False):
            file_ids = self.data["file_ids"]
        elif self.data["file_id"]:
            file_ids = [self.data["file_id"]]
        else:
            LOGGER.warning("No file set in the DataBlock")
            return

        if not file_ids:
            return
        if len(file_ids) == 1:
            self.data["bokeh_plot_data"] = self._plot_data_for_one_file(file_ids[0])
        elif len(file_ids) > 2:
            LOGGER.warning("This datablock does not currently support more than two files")
            return
        else:
            self.data["bokeh_plot_data"] = self._plot_data_for_two_files(file_ids[0], file_ids[1])

    def _get_and_check_ext(self, file_info):
        ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
        if ext not in self.accepted_file_extensions:
            LOGGER.warning(
                "Unsupported file extension (must be one of %s, not %s)",
                self.accepted_file_extensions,
                ext,
            )
        return ext, ext in self.accepted_file_extensions

    def _plot_data_for_one_file(self, file_id):

        file_info = get_file_info_by_id(file_id, update_if_live=True)
        ext, acceptable = self._get_and_check_ext(file_info)
        if ext == ".asc":
            ms_data = parse_mt_mass_spec_ascii(Path(file_info["location"]))
            if ms_data:
                return self._plot_ms_data(ms_data)
        elif ext == ".txt":
            ms_data = parse_mt_mass_spec_txt(Path(file_info["location"]))
            if ms_data:
                return self._plot_ms_txt_data(ms_data)
        return None

    def _plot_data_for_two_files(self, file_id0, file_id1):
        file_info_0 = get_file_info_by_id(file_id0, update_if_live=True)
        file_info_1 = get_file_info_by_id(file_id1, update_if_live=True)
        ext_0, acceptable_0 = self._get_and_check_ext(file_info_0)
        ext_1, acceptable_1 = self._get_and_check_ext(file_info_1)
        exts = [ext_0, ext_1]
        if not (acceptable_0 and acceptable_1) or not (".asc" in exts and ".txt" in exts):
            LOGGER.warning(
                "When using two files with this datablock, "
                "one file with .asc and another file with .txt are required"
            )
            return None

        if ext_0 == ".asc":
            ms_asc_data = parse_mt_mass_spec_ascii(Path(file_info_0["location"]))
            ms_txt_data = parse_mt_mass_spec_txt(Path(file_info_1["location"]))
            return self._plot_txt_and_asc_data(ms_asc_data, ms_txt_data)
        else:
            ms_asc_data = parse_mt_mass_spec_ascii(Path(file_info_1["location"]))
            ms_txt_data = parse_mt_mass_spec_txt(Path(file_info_0["location"]))
            return self._plot_txt_and_asc_data(ms_asc_data, ms_txt_data)

    def _plot_txt_and_asc_data(self, ms_asc_data, ms_txt_data):
        """
        Plots txt and asc data together
        Parameters:
            ms_asc_data: partial pressures data
            ms_txt_data: differential thermal analysis data
        """
        tsc = ms_txt_data["data"]["tga"]["Ts[°C]"]
        trc = ms_txt_data["data"]["tga"]["Tr[°C]"]
        ts = ms_txt_data["data"]["tga"]["t[s]"]
        f_tsc = scipy.interpolate.interp1d(
            ts, tsc, kind="nearest", fill_value=None, bounds_error=False
        )
        f_trc = scipy.interpolate.interp1d(
            ts, trc, kind="nearest", fill_value=None, bounds_error=False
        )
        for species in ms_asc_data["data"]:
            ms_asc_data["data"][species]["Ts[°C]"] = f_tsc(
                ms_asc_data["data"][species]["Time Relative [s]"]
            )
            ms_asc_data["data"][species]["Tr[°C]"] = f_trc(
                ms_asc_data["data"][species]["Time Relative [s]"]
            )

        return self._plot_ms_data(ms_asc_data, include_x_temperature=True, dta_data=ms_txt_data)

    @classmethod
    def _plot_ms_data(cls, ms_data, include_x_temperature=False, dta_data=None):
        x_options = ["Time Relative [s]"]
        if include_x_temperature:
            x_options.extend(["Ts[°C]", "Tr[°C]"])

        # collect the maximum value of the data key for each species for plot ordering
        max_vals: list[tuple[str, float]] = []

        data_key: str = (
            "Partial pressure [mbar] or Ion Current [A]"  # default value for data key if missing
        )

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
            plots[-1].children[0].xaxis[0].ticker.desired_num_ticks = 4
        if include_x_temperature:
            plots.append(
                selectable_axes_plot(
                    dta_data["data"]["tga"],
                    x_options=["Ts[°C]", "Tr[°C]"],
                    y_options=["Value[mg]"],
                    plot_line=True,
                    plot_points=False,
                    plot_title="Differential thermal analysis (DTA)",
                    aspect_ratio=1.5,
                )
            )

        # construct MxN grid of all species
        M = 3
        grid = []
        for i in range(0, len(plots), M):
            grid.append(plots[i : i + M])
        p = gridplot(grid, sizing_mode="scale_width", toolbar_location="below")

        return bokeh.embed.json_item(p, theme=DATALAB_BOKEH_GRID_THEME)

    @classmethod
    def _plot_ms_txt_data(cls, ms_data):
        x_options = ["Ts[°C]", "t[s]", "Tr[°C]"]
        y_options = ["Value[mg]"]
        plot = selectable_axes_plot(
            ms_data["data"]["tga"],
            x_options=x_options,
            y_options=y_options,
            plot_line=True,
            plot_points=False,
            plot_title="Differential Thermal Analysis (DTA)",
        )
        return bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_GRID_THEME)
