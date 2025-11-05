import os
from pathlib import Path

import bokeh.embed
import pandas as pd
from bokeh.models import HoverTool, LogColorMapper

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


def parse_ivium_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    column_map = {
        "Z1 /ohm": "Re(Z) [Ω]",
        "Z2 /ohm": "-Im(Z) [Ω]",
        "freq. /Hz": "Frequency [Hz]",
    }

    if not all(k in eis.columns for k in column_map):
        raise RuntimeError(
            f"File does not appear to be a valid Ivium EIS export, expected columns {column_map.keys()}, found {eis.columns}"
        )

    eis["Z2 /ohm"] *= -1
    eis.rename(
        column_map,
        inplace=True,
        axis="columns",
    )
    return eis


def parse_pstrace_eis_txt(filename: Path):
    eis = pd.read_csv(filename, sep="\t")

    column_map = {
        "Frequency": "Frequency [Hz]",
        "Zdash": "Re(Z) [Ω]",
        "Zdashneg": "-Im(Z) [Ω]",
        "Z": "|Z| [Ω]",
        "Phase": "θ [°]",
        "Y": "|Y| [S]",
        "YRe": "Re(Y) [S]",
        "YIm": "Im(Y) [S]",
        "Cdash": "Re(C) [F]",
        "Cdashdash": "Im(C) [F]",
    }

    if not all(k in eis.columns for k in column_map):
        raise RuntimeError(
            f"File does not appear to be a valid PSTrace EIS export, expected columns {column_map.keys()}, found {eis.columns}"
        )

    eis.rename(
        column_map,
        inplace=True,
        axis="columns",
    )
    return eis


class EISBlock(DataBlock):
    accepted_file_extensions = (".txt",)
    blocktype = "eis"
    name = "EIS"
    description = """
This block can plot electrochemical impedance spectroscopy (EIS) data from:

- exported  Ivium .txt files
- exported .txt files from PSTrace.
    """

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

            errors = []
            eis_data = None
            try:
                eis_data = parse_ivium_eis_txt(Path(file_info["location"]))
            except RuntimeError as exc:
                errors = [exc]

            try:
                eis_data = parse_pstrace_eis_txt(Path(file_info["location"]))
            except RuntimeError as exc:
                errors.append(exc)

            if eis_data is None:
                raise RuntimeError(
                    f"Could not parse EIS data from uploaded file with implemented parsers. Errors: {errors}"
                )

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
