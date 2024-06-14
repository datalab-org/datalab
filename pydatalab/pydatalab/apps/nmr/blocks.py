import os
import zipfile

import bokeh.embed
import pandas as pd

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

from .utils import read_bruker_1d


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

    def read_bruker_nmr_data(self):
        if "file_id" not in self.data:
            LOGGER.warning("NMRPlot.read_bruker_nmr_data(): No file set in the DataBlock")
            return

        zip_file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        filename = zip_file_info["name"]

        name, ext = os.path.splitext(filename)
        if ext.lower() not in self.accepted_file_extensions:
            LOGGER.warning(
                "NMRBlock.read_bruker_nmr_data(): Unsupported file extension (must be .zip)"
            )
            return

        # unzip:
        directory_location = zip_file_info["location"] + ".extracted"
        LOGGER.debug(f"Directory location is: {directory_location}")
        with zipfile.ZipFile(zip_file_info["location"], "r") as zip_ref:
            zip_ref.extractall(directory_location)

        extracted_directory_name = os.path.join(directory_location, name)
        available_processes = os.listdir(os.path.join(extracted_directory_name, "pdata"))

        if self.data.get("selected_process") not in available_processes:
            self.data["selected_process"] = available_processes[0]

        try:
            df, a_dic, topspin_title, processed_data_shape = read_bruker_1d(
                os.path.join(directory_location, name),
                process_number=self.data["selected_process"],
                verbose=False,
            )
        except Exception as error:
            LOGGER.critical(f"Unable to parse {name} as Bruker project. {error}")
            return

        serialized_df = df.to_dict() if (df is not None) else None

        # all data sorted in a fairly raw way
        self.data["processed_data"] = serialized_df
        self.data["acquisition_parameters"] = a_dic["acqus"]
        self.data["processing_parameters"] = a_dic["procs"]
        self.data["pulse_program"] = a_dic["pprog"]

        # specific things that we might want to pull out for the UI:
        self.data["available_processes"] = available_processes
        self.data["nucleus"] = a_dic["acqus"]["NUC1"]
        self.data["carrier_frequency_MHz"] = a_dic["acqus"]["SFO1"]
        self.data["carrier_offset_Hz"] = a_dic["acqus"]["O1"]
        self.data["recycle_delay"] = a_dic["acqus"]["D"][1]
        self.data["nscans"] = a_dic["acqus"]["NS"]
        self.data["CNST31"] = a_dic["acqus"]["CNST"][31]
        self.data["processed_data_shape"] = processed_data_shape

        self.data["probe_name"] = a_dic["acqus"]["PROBHD"]
        self.data["pulse_program_name"] = a_dic["acqus"]["PULPROG"]
        self.data["topspin_title"] = topspin_title

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
