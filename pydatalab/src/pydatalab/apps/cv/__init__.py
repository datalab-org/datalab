import os
from pathlib import Path

import bokeh.embed
from bokeh.models import HoverTool

from pydatalab.apps.cv.utils import _split_by_cycle, parse_chi_cv_txt, parse_cv_mpr
from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class CVBlock(DataBlock):
    accepted_file_extensions: tuple[str, ...] = (".mpr", ".txt")
    blocktype = "cv"
    name = "Cyclic Voltammetry"
    description = (
        "This block can plot CV data from:\n\n"
        "- .mpr files from Biologic potentiostats\n"
        "- .txt files from CH Instruments potentiostats\n"
    )

    @property
    def plot_functions(self):
        return (self.generate_cv_plot,)

    def generate_cv_plot(self):
        if "file_id" not in self.data:
            return

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
        if ext not in self.accepted_file_extensions:
            LOGGER.warning(
                "Unsupported file extension (must be one of %s, not %s)",
                self.accepted_file_extensions,
                ext,
            )
            return

        if ext == ".mpr":
            cv_data = _split_by_cycle(parse_cv_mpr(Path(file_info["location"])))
        elif ext == ".txt":
            cv_data = _split_by_cycle(parse_chi_cv_txt(Path(file_info["location"])))

        n_cycles = len(cv_data)
        hover = HoverTool(
            tooltips=[
                ("Potential", "@{Potential (V)}{0.00} V"),
                ("Current", "@{Current (mA)}{0.0000} mA"),
                ("Cycle", "@{Cycle}"),
            ],
            mode="mouse",
        )

        cycle_numbers = [df["Cycle"].iloc[0] for df in cv_data.values()]

        layout = selectable_axes_plot(
            cv_data,
            x_options=["Potential (V)"],
            y_options=["Current (mA)"],
            series_color_values=cycle_numbers if n_cycles > 8 else None,
            series_color_label="Cycle" if n_cycles > 8 else None,
            plot_points=False,
            plot_line=True,
            use_unique_labels=False,
            tools=hover,
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
