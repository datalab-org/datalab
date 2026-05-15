import os
from pathlib import Path

import bokeh.embed
from bokeh.models import HoverTool

from pydatalab.apps.cv.utils import _split_by_cycle, parse_chi_cv_txt, parse_cv_mpr

# Number of cycles above which continuous Viridis coloring is used instead of discrete Dark2
CONTINUOUS_COLORMAP_THRESHOLD = 8
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

    @classmethod
    def _format_cv_plot(cls, cv_data: dict, tools=None):
        """Build and return a selectable_axes_plot layout for CV data.

        Args:
            cv_data: Dict mapping cycle labels to per-cycle DataFrames, each with
                columns "Potential (V)", "Current (mA)", and "Cycle".
            tools: Optional extra Bokeh tool(s) to pass to selectable_axes_plot.

        Returns:
            A Bokeh layout as returned by selectable_axes_plot.
        """
        n_cycles = len(cv_data)
        cycle_numbers = [df["Cycle"].iloc[0] for df in cv_data.values()]
        use_continuous = n_cycles > CONTINUOUS_COLORMAP_THRESHOLD
        return selectable_axes_plot(
            cv_data,
            x_options=["Potential (V)"],
            y_options=["Current (mA)"],
            series_color_values=cycle_numbers if use_continuous else None,
            series_color_label="Cycle" if use_continuous else None,
            plot_points=False,
            plot_line=True,
            use_unique_labels=False,
            tools=tools,
        )

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
        else:
            return

        if len(cv_data) == 0:
            LOGGER.warning("Parsed CV data contains no rows")
            return

        hover = HoverTool(
            tooltips=[
                ("Potential", "@{Potential (V)}{0.00} V"),
                ("Current", "@{Current (mA)}{0.0000} mA"),
                ("Cycle", "@{Cycle}"),
            ],
            mode="mouse",
        )

        layout = self._format_cv_plot(cv_data, tools=hover)
        self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
