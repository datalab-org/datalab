import os
from pathlib import Path

import bokeh.embed
import pandas as pd
from bokeh.models import HoverTool, LogColorMapper
from galvani import MPRfile

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


def parse_biologic_mpr(filename: Path):
    mpr_file = MPRfile(str(filename))
    return pd.DataFrame(
        {
            "Frequency [Hz]": mpr_file.data["freq/Hz"],
            "Re(Z) [Ω]": mpr_file.data["Re(Z)/Ohm"],
            "-Im(Z) [Ω]": mpr_file.data["-Im(Z)/Ohm"],
        }
    )


class EISBlock(DataBlock):
    accepted_file_extensions = (".txt", ".mpr")
    blocktype = "eis"
    name = "EIS"
    description = """
This block can plot electrochemical impedance spectroscopy (EIS) data from:

- exported  Ivium .txt files
- exported .txt files from PSTrace.
- .mpr files from biologic.
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
        elif ext == ".txt":
            for parser in (parse_ivium_eis_txt, parse_pstrace_eis_txt):
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
