import os
from pathlib import Path

import bokeh.embed
import numpy as np
import pandas as pd
from bokeh.models import HoverTool, LogColorMapper

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class UVVisBlock(DataBlock):
    accepted_file_extensions = (".txt",)
    blocktype = "uvvis"
    name = "UV-Vis"
    description = (
        "This block can plot UV-Vis data from a .txt file. "
        "Two files are required, the scan to plot and the background scan."
    )

    @property
    def plot_functions(self):
        return (self.generate_absorbance_plot,)

    @classmethod
    def parse_uvvis_txt(self, filename: Path) -> pd.DataFrame:
        """
        Parses a UV-Vis .txt file into a pandas DataFrame
        Args:
            filename (Path): Path to the .txt file
        Returns:
            pd.DataFrame: DataFrame containing the UV-Vis data with columns for wavelength and absorbance
        """
        # Read the file, skipping the first 7 rows and using the first row as header
        data = pd.read_csv(filename, sep=r";", skiprows=7, header=None)

        # I need to look into what dark counts and reference counts are - I never used them just the sample counts from two differernt runs
        data.columns = ["Wavelength", "Sample counts", "Dark counts", "Reference counts"]
        return data

    @classmethod
    def find_absorbance(self, data_df, reference_df):
        """
        Calculates the absorbance from the sample and reference dataframes
        Args:
            data_df (pd.DataFrame): DataFrame containing the sample data
            reference_df (pd.DataFrame): DataFrame containing the reference data
        Returns:
            pd.DataFrame: DataFrame containing the absorbance data
        """
        # Calculate absorbance using Beer-Lambert Law
        absorbance = -np.log10(data_df["Sample counts"] / reference_df["Sample counts"])
        # Create a new DataFrame with the wavelength and absorbance
        absorbance_data = pd.DataFrame(
            {"Wavelength": data_df["Wavelength"], "Absorbance": absorbance}
        )
        return absorbance_data

    @classmethod
    def _format_UV_Vis_plot(self, absorbance_data: pd.DataFrame) -> bokeh.layouts.layout:
        """
        Formats the UV-Vis plot using Bokeh
        Args:
            absorbance_data (pd.DataFrame): DataFrame containing the wavelength and absorbance data
        Returns:
            bokeh.layouts.layout: Bokeh layout object containing the plot
        """
        # Create a Bokeh plot with selectable axes
        layout = selectable_axes_plot(
            absorbance_data,
            x_options=["Wavelength"],
            y_options=["Absorbance"],
            color_mapper=LogColorMapper("Cividis256"),
            plot_points=False,
            plot_line=True,
            tools=HoverTool(
                tooltips=[
                    ("Wavelength / nm", "@Wavelength{0.00}"),
                    ("Absorbance", "@Absorbance{0.0000}"),
                ],  # Display x and y values to specified decimal places
                mode="vline",  # Ensures hover follows the x-axis
            ),
        )
        # Adding cm^-1 to the x-axis label using unicode characters - might be a more logical way
        layout.children[1].xaxis.axis_label = "Wavelength / nm"
        return layout

    def generate_absorbance_plot(self):
        sample_file_info = None
        reference_file_info = None
        # all_files = None
        absorbance_data = None

        if "sample_file_id" not in self.data or "reference_file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return
        else:
            sample_file_info = get_file_info_by_id(self.data["sample_file_id"], update_if_live=True)
            ext = os.path.splitext(sample_file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )

            reference_file_info = get_file_info_by_id(
                self.data["reference_file_id"], update_if_live=True
            )
            ext = os.path.splitext(reference_file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )
                return

            sample_data = self.parse_uvvis_txt(Path(sample_file_info["location"]))
            reference_data = self.parse_uvvis_txt(Path(reference_file_info["location"]))
            if sample_data is None or reference_data is None:
                LOGGER.warning("Could not parse the UV-Vis data files")
                return
            # Calculate absorbance
            absorbance_data = self.find_absorbance(sample_data, reference_data)

        if absorbance_data is not None:
            LOGGER.info("Generating UV-Vis plot")
            layout = self._format_UV_Vis_plot(absorbance_data)
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
