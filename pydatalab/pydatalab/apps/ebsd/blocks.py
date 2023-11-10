import os
from pathlib import Path
from typing import List, Tuple

import bokeh
import pandas as pd

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import mytheme, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id


class EBSDBlock(DataBlock):
    blocktype = "ebsd"
    description = "Electron backscatter diffraction microscopy"
    accepted_file_extensions = (".ctf",)

    @property
    def plot_functions(self):
        return (self.generate_ebsd_plot,)

    @classmethod
    def load(self, location: str | Path) -> Tuple[pd.DataFrame, List[str]]:
        if not isinstance(location, str):
            location = str(location)
        ext = os.path.splitext(location)[-1].lower()

        if ext not in self.accepted_file_extensions:
            raise RuntimeError(
                f"Cannot make use of file {location!r}, need extension {self.accepted_file_extensions}"
            )

        with open(location, "r") as f:
            header_lines = []
            line = f.readline()

            # First check for magic header line
            if "Channel Text File" not in line:
                raise RuntimeError(
                    f"Could not interpret {location!r} as a Channel Text File (CTF) - missing header."
                )

            # Then scrape everything up to the "Phases N"  definition
            while line := f.readline():
                if "Phases\t" in line:
                    break
                header_lines.append(line)
            else:
                raise RuntimeError(
                    f"Could not interpret {location!r} as a Channel Text File (CTF) - missing phase definition."
                )

            num_phases = int(line.strip().split("\t")[-1])

            # Then scrape the phase definitions themselves
            phases = []
            counter = 0
            while (line := f.readline()) and counter <= num_phases:
                if "Phase\tX\tY" in line:
                    column_location = f.tell()
                    break
                phases.append(line)
                counter += 1
            else:
                raise RuntimeError(
                    f"Could not interpret {location} as a Channel Text File (CTF) - missing phase data. Read {counter} phases of expected {num_phases}."
                )

            # Finally we get to the actual data, which should fill the rest of the file
            columns = line.strip().split("\t")

            # Rewind the file back to include the column header, then make sure they match
            f.seek(column_location)
            df = pd.read_csv(f, delimiter="\t", names=columns)
            return df, phases

    def generate_ebsd_plot(self):
        file_info = None
        df = None

        if "file_id" not in self.data:
            return None

        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                raise RuntimeError(
                    "Unsupported file extension (must be one of %s), not %s",
                    self.accepted_file_extensions,
                    ext,
                )
            df, _ = self.load(file_info["location"])

        column_map = {
            "BC": "Band contrast",
            "BS": "Band slope",
            "X": "x (nm)",
            "Y": "y (nm)",
        }
        df.rename(columns=column_map, inplace=True)

        if not df.empty:
            p = selectable_axes_plot(
                df,
                x_options=["x (nm)"],
                y_options=["y (nm)"],
                color_options=[
                    "Band contrast",
                    "Band slope",
                    "Phase",
                    "Bands",
                ],
                plot_line=False,
                plot_points=True,
                match_aspect=True,
                plot_width=800,
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)
