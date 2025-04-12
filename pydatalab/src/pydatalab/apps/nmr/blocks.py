import os
import tempfile
import zipfile
from pathlib import Path

import bokeh.embed
import pandas as pd

from pydatalab.apps.nmr.utils import read_bruker_1d
from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id


class NMRBlock(DataBlock):
    blocktype = "nmr"
    name = "NMR"
    description = "A simple NMR block for visualizing 1D NMR data from Bruker projects."

    accepted_file_extensions = (".zip",)
    defaults = {"process number": 1}
    _supports_collections = False

    @property
    def plot_functions(self):
        return (self.generate_nmr_plot,)

    def read_bruker_nmr_data(self) -> tuple[dict | None, dict]:
        if "file_id" not in self.data:
            raise RuntimeError("No file set in the DataBlock")

        zip_file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        filename = zip_file_info["name"]

        name, ext = os.path.splitext(filename)
        if ext.lower() not in self.accepted_file_extensions:
            raise RuntimeError(
                f"Unsupported file extension {ext.lower()} (must be one of {self.accepted_file_extensions})"
            )

        # unzip to tmp directory
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a Path object for the temporary directory
            tmpdir_path = Path(tmpdirname)

            # Unzip the file to the temporary directory
            with zipfile.ZipFile(zip_file_info["location"], "r") as zip_ref:
                zip_ref.extractall(tmpdir_path)

            extracted_directory_name = tmpdir_path / name
            available_processes = os.listdir(os.path.join(extracted_directory_name, "pdata"))

            if self.data.get("selected_process") not in available_processes:
                self.data["selected_process"] = available_processes[0]

            try:
                df, a_dic, topspin_title, processed_data_shape = read_bruker_1d(
                    tmpdir_path / name,
                    process_number=self.data["selected_process"],
                    verbose=False,
                )
            except Exception as error:
                raise RuntimeError(f"Unable to parse {name!r} as Bruker project. Error: {error!r}")

        serialized_df = df.to_dict() if (df is not None) else None

        metadata = {}
        metadata["acquisition_parameters"] = a_dic["acqus"]
        metadata["processing_parameters"] = a_dic["procs"]
        metadata["pulse_program"] = a_dic["pprog"]
        metadata["available_processes"] = available_processes
        metadata["nucleus"] = a_dic["acqus"]["NUC1"]
        metadata["carrier_frequency_MHz"] = a_dic["acqus"]["SFO1"]
        metadata["carrier_offset_Hz"] = a_dic["acqus"]["O1"]
        metadata["recycle_delay"] = a_dic["acqus"]["D"][1]
        metadata["nscans"] = a_dic["acqus"]["NS"]
        metadata["CNST31"] = a_dic["acqus"]["CNST"][31]
        metadata["processed_data_shape"] = processed_data_shape
        metadata["probe_name"] = a_dic["acqus"]["PROBHD"]
        metadata["pulse_program_name"] = a_dic["acqus"]["PULPROG"]
        metadata["topspin_title"] = topspin_title

        self.data["metadata"] = metadata
        self.data["processed_data"] = serialized_df

        return serialized_df, metadata

    def generate_nmr_plot(self):
        # currently calls every time plotting happens, but it should only happen if the file was updated
        self.read_bruker_nmr_data()
        if "processed_data" not in self.data or not self.data["processed_data"]:
            self.data["bokeh_plot_data"] = None
            return

        df = pd.DataFrame(self.data["processed_data"])
        df["normalized intensity"] = df.intensity / df.intensity.max()

        bokeh_layout = selectable_axes_plot(
            df,
            x_options=["ppm", "hz"],
            y_options=[
                "intensity",
                "intensity_per_scan",
                "normalized intensity",
            ],
            plot_line=True,
            point_size=3,
        )
        # flip x axis, per NMR convention. Note that the figure is the second element
        # of the layout in the current implementation, but this could be fragile.
        bokeh_layout.children[1].x_range.flipped = True

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(
            bokeh_layout, theme=DATALAB_BOKEH_THEME
        )
