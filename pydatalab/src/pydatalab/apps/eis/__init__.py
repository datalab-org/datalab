import os
from pathlib import Path

import bokeh.embed
from bokeh.models import HoverTool, LogColorMapper

from pydatalab.apps.eis.utils import (
    parse_biologic_mpr,
    parse_ivium_eis_txt,
    parse_ivium_eis_txt_no_header,
    parse_palmsens_pssession,
    parse_pstrace_eis_txt,
)
from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class EISBlock(DataBlock):
    accepted_file_extensions = (".txt", ".mpr", ".pssession")
    blocktype = "eis"
    name = "EIS"
    description = """
This block can plot electrochemical impedance spectroscopy (EIS) data from:

- exported  Ivium .txt files
- exported .txt files from PSTrace.
- .mpr files from Biologic.
- .pssession files from PalmSens.
    """

    @property
    def plot_functions(self):
        return (self.generate_eis_plot,)

    def generate_eis_plot(self):
        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
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

        errors = []
        eis_data = None

        if ext == ".mpr":
            try:
                eis_data = parse_biologic_mpr(Path(file_info["location"]))
            except RuntimeError as exc:
                errors = [exc]
        elif ext == ".pssession":
            try:
                eis_data = parse_palmsens_pssession(Path(file_info["location"]))
            except RuntimeError as exc:
                errors = [exc]
        elif ext == ".txt":
            for parser in (
                parse_ivium_eis_txt,
                parse_pstrace_eis_txt,
                parse_ivium_eis_txt_no_header,
            ):
                try:
                    eis_data = parser(Path(file_info["location"]))
                    break
                except RuntimeError as exc:
                    errors.append(exc)

        if eis_data is None:
            raise RuntimeError(
                f"Could not parse EIS data from uploaded file with implemented parsers. Errors: {errors}"
            )

        numeric_cols = list(eis_data.select_dtypes("number").columns)
        plot = selectable_axes_plot(
            eis_data,
            x_options=["Re(Z) [Ω]"] + [c for c in numeric_cols if c != "Re(Z) [Ω]"],
            y_options=["-Im(Z) [Ω]"] + [c for c in numeric_cols if c != "-Im(Z) [Ω]"],
            y_default="-Im(Z) [Ω]",
            color_options=["Frequency [Hz]"],
            color_mapper=LogColorMapper("Cividis256"),
            plot_points=True,
            plot_line=False,
            tools=HoverTool(tooltips=[("Frequency [Hz]", "@{Frequency [Hz]}")]),
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)
