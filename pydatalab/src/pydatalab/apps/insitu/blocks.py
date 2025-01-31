import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bokeh.embed
import numpy as np
import pandas as pd
from bokeh.layouts import row
from bokeh.models import ColorBar, LinearColorMapper, Range1d
from bokeh.plotting import figure
from datalab_app_plugin_nmr_insitu import process_data

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class InsituBlock(DataBlock):
    blocktype = "insitu"
    name = "NMR insitu"
    description = "A simple NMR insitu block from .zip files."
    accepted_file_extensions = (".zip",)
    nmr_folder_name = ""
    echem_folder_name = ""

    defaults = {
        "ppm1": 220,
        "ppm2": 310,
        "start_exp": 1,
        "exclude_exp": None,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.data, "get"):
            self.data = {}
        for key, value in self.defaults.items():
            self.data.setdefault(key, value)

    @property
    def plot_functions(self):
        return (self.generate_insitu_nmr_plot,)

    def _validate_parameters(self) -> bool:
        """Validate input parameters before processing."""
        try:
            float(self.data.get("ppm1", self.defaults["ppm1"]))
            float(self.data.get("ppm2", self.defaults["ppm2"]))
            return True
        except ValueError:
            LOGGER.error("Invalid PPM values provided")
            return False

    def process_and_store_data(self) -> bool:
        """Process insitu NMR and electrochemical data and store results."""
        if not self._validate_parameters():
            return False

        try:
            ppm1 = float(self.data.get("ppm1", self.defaults["ppm1"]))
            ppm2 = float(self.data.get("ppm2", self.defaults["ppm2"]))

            nmr_folder_name = self.data.get("nmr_folder_name")
            echem_folder_name = self.data.get("echem_folder_name")
            start_exp = int(self.data.get("start_exp", self.defaults["start_exp"]))
            exclude_exp = self.data.get("exclude_exp", self.defaults["exclude_exp"])
            api_url = os.environ.get("DATALAB_API_URL")
            if not api_url:
                raise ValueError(
                    "API URL is missing. Please set the 'DATALAB_API_URL' environment variable."
                )

            result = process_data(
                api_url=api_url,
                item_id="bc_insitu_block",
                folder_name="Example-TEGDME.zip",
                nmr_folder_name=nmr_folder_name,
                echem_folder_name=echem_folder_name,
                ppm1=ppm1,
                ppm2=ppm2,
                start_at=start_exp,
                exclude_exp=exclude_exp,
            )

            self.data.update(
                {
                    "nmr_data": result["nmr_spectra"],
                    "echem_data": result["echem"],
                    "metadata": result["metadata"],
                    "processing_params": {
                        "ppm1": ppm1,
                        "ppm2": ppm2,
                        "file_id": self.data.get("file_id"),
                        "start_exp": start_exp,
                        "exclude_exp": exclude_exp,
                    },
                }
            )

            return True

        except Exception as e:
            LOGGER.error(f"Error processing data: {str(e)}")
            return False

    def should_reprocess_data(self) -> bool:
        """Determine if data needs to be reprocessed based on parameter changes."""
        if "processing_params" not in self.data:
            return True

        params = self.data["processing_params"]
        current_params = {
            "ppm1": float(self.data.get("ppm1", self.defaults["ppm1"])),
            "ppm2": float(self.data.get("ppm2", self.defaults["ppm2"])),
            "file_id": self.data.get("file_id"),
            "start_exp": int(self.data.get("start_exp", self.defaults["start_exp"])),
            "exclude_exp": self.data.get("exclude_exp", self.defaults["exclude_exp"]),
        }

        return (
            any(params.get(key) != current_params[key] for key in current_params)
            or "nmr_data" not in self.data
        )

    def generate_insitu_nmr_plot(
        self, ppm1: Optional[float] = None, ppm2: Optional[float] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Generate combined NMR and electrochemical plots."""
        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return None, []

        try:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            if Path(file_info["location"]).suffix.lower() not in self.accepted_file_extensions:
                LOGGER.warning(
                    f"Unsupported file extension (must be one of {self.accepted_file_extensions})"
                )
                return None, []

            if self.should_reprocess_data():
                LOGGER.info("Processing new data...")
                if not self.process_and_store_data():
                    return None, []
            else:
                LOGGER.info("Using stored data...")

            nmr_data = self.data["nmr_data"]
            echem_data = self.data["echem_data"]
            metadata = self.data["metadata"]

            y_start = metadata["time_range"]["start"]
            y_end = metadata["time_range"]["end"]
            shared_y_range = Range1d(start=y_start, end=y_end)

            echem_plot = self._create_echem_plot(echem_data, y_range=shared_y_range)

            nmr_plot = self._create_nmr_heatmap(
                nmr_data, metadata["ppm_range"], metadata["time_range"], y_range=shared_y_range
            )

            combined_plot = row(echem_plot, nmr_plot)

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(
                combined_plot, theme=DATALAB_BOKEH_THEME
            )

            return self.data.get("time_data"), ["Plot successfully generated"]

        except Exception as e:
            LOGGER.error(f"Error in generate_insitu_nmr_plot: {str(e)}")
            return None, []

    def _create_echem_plot(self, echem_data: pd.DataFrame, y_range: Range1d) -> figure:
        """Create electrochemical plot."""
        plot = figure(
            x_axis_label="Voltage",
            y_axis_label="Time (h)",
            plot_height=700,
            plot_width=400,
            y_range=y_range,
            min_border_right=0,
        )

        plot.line(echem_data["Voltage"], echem_data["time"], line_color="blue")

        return plot

    def _create_nmr_heatmap(
        self,
        nmr_data: Dict,
        ppm_range: Dict[str, float],
        time_range: Dict[str, float],
        y_range: Range1d,
    ) -> figure:
        """Create NMR heatmap plot."""
        plot = figure(
            x_axis_label="ppm",
            plot_height=700,
            plot_width=400,
            y_axis_location="right",
            x_range=Range1d(start=ppm_range["end"], end=ppm_range["start"]),
            y_range=y_range,
            min_border_left=0,
        )

        intensity_matrix = np.array([spectrum["intensity"] for spectrum in nmr_data["spectra"]])

        color_mapper = LinearColorMapper(
            palette="Turbo256", low=intensity_matrix.min(), high=intensity_matrix.max()
        )

        plot.image(
            image=[intensity_matrix],
            x=ppm_range["end"],
            y=time_range["start"],
            dw=ppm_range["end"] - ppm_range["start"],
            dh=time_range["end"] - time_range["start"],
            color_mapper=color_mapper,
        )

        plot.add_layout(ColorBar(color_mapper=color_mapper, location=(0, 0)), "right")

        return plot
