import warnings
from pathlib import Path

import bokeh.embed
import pandas as pd
from bokeh.models import HoverTool

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id

from .utils import find_absorbance, parse_uvvis_txt


class UVVisBlock(DataBlock):
    accepted_file_extensions = (".Raw8.txt", ".txt")
    blocktype = "uv-vis"
    name = "UV-Vis"
    description = (
        "This block can plot UV-Vis data from a .txt file. "
        "Two files are required, the scan to plot and the background scan.\n"
        "The first file in the order will be treated as the background scan, and subsequent files as the sample scans."
    )

    @property
    def plot_functions(self):
        return (self.generate_absorbance_plot,)

    @classmethod
    def _format_UV_Vis_plot(
        self, absorbance_data_list: list[pd.DataFrame], names: list[str] | None = None
    ) -> bokeh.layouts.layout:
        """
        Formats a UV-Vis plot for one or more spectra using the selectable_axes_plot function.

        Args:
            absorbance_data_list (list[pd.DataFrame]): List of DataFrames, each required
                                                     to have 'Wavelength' and 'Absorbance' columns.
            names (list[str], optional): A list of names corresponding to each DataFrame,
                                         used for the legend. If provided, its length must match
                                         the length of absorbance_data_list.

        Returns:
            bokeh.layouts.layout or None: Bokeh layout object containing the plot and controls,
                                          as returned by selectable_axes_plot. Returns None if
                                          input list is empty or plotting is skipped internally.
        """
        if not absorbance_data_list:
            warnings.warn("Received an empty list of absorbance data. No plot generated.")
            return None

        # Basic validation of input data structure
        if names and len(names) != len(absorbance_data_list):
            raise ValueError("Length of 'names' list must match the number of DataFrames.")

        for i, df in enumerate(absorbance_data_list):
            if not {"Wavelength", "Absorbance"}.issubset(df.columns):
                raise ValueError(
                    f"DataFrame at index {i} must contain 'Wavelength' and 'Absorbance' columns."
                )

        if names:
            # Use provided names as keys
            plot_data_input = {
                str(name): df for name, df in zip(names, absorbance_data_list)
            }  # Ensure names are strings
        else:
            # Generate default names if none provided, ensuring keys are strings
            plot_data_input = {f"Spectrum {i + 1}": df for i, df in enumerate(absorbance_data_list)}

        # Define the specific HoverTool configuration needed for UV-Vis
        uv_hover_tool = HoverTool(
            # Ensure these column names (@Wavelength, @Absorbance) exist in the DataFrames
            tooltips=[
                ("Wavelength / nm", "@Wavelength{0.00}"),
                ("Absorbance", "@Absorbance{0.0000}"),
                # Note: selectable_axes_plot doesn't automatically add the dict key/name
                # as a column to the CDS, so we can't easily use ('Name', '@name')
                # unless we modify selectable_axes_plot or preprocess the data.
                # The legend will be the primary identifier.
            ],
            mode="vline",  # Tooltip follows the x-coordinate across all lines
        )
        # Call the existing selectable_axes_plot function
        # We configure it specifically for a non-selectable UV-Vis plot use case
        layout = selectable_axes_plot(
            df=plot_data_input,  # Pass the list or dict of DataFrames
            x_options=["Wavelength"],  # Fix X axis option
            y_options=["Absorbance"],  # Fix Y axis option
            x_default="Wavelength",  # Set default X
            y_default="Absorbance",  # Set default Y
            plot_points=False,  # We only want lines for spectra
            plot_line=True,  # Ensure lines are plotted
            tools=[uv_hover_tool],  # Add our specific hover tool
            # color_options / color_mapper: Let selectable_axes_plot handle default color cycling
            #                                based on index unless specific coloring logic is needed.
            # plot_title="UV-Vis Spectra", # Optional: Add a title if desired
            show_table=False,  # Usually don't need the table for this plot type
        )
        # Adding cm^-1 to the x-axis label using unicode characters - might be a more logical way
        layout.children[0].xaxis.axis_label = "Wavelength / nm"
        return layout

    def generate_absorbance_plot(self):
        absorbance_data = None
        if "selected_file_order" not in self.data:
            warnings.warn("No file set in the DataBlock - selected_file_order")
            return

        else:
            file_info = []
            for file_id in self.data["selected_file_order"]:
                file_info.append(get_file_info_by_id((file_id), update_if_live=True))

            if len(file_info) < 2:
                warnings.warn("Not enough files selected - at least 2 required")
                return
            # Check if the file is in the accepted file extensions
            for file in file_info:
                ext = "".join(Path(file["location"]).suffixes).lower()
                # ext = os.path.splitext(file["location"].split("/")[-1])[-1].lower()
                if ext not in {ext.lower() for ext in self.accepted_file_extensions}:
                    raise ValueError(
                        f"Unsupported file extension (must be one of {self.accepted_file_extensions}, not {ext})"
                    )

            reference_data = parse_uvvis_txt(Path(file_info[0]["location"]))
            absorbance_data = []
            for file in file_info[1:]:
                sample_data = parse_uvvis_txt(Path(file["location"]))
                if sample_data is None or reference_data is None:
                    warnings.warn("Could not parse the UV-Vis data files")
                    return
                # Calculate absorbance
                absorbance_data.append(find_absorbance(sample_data, reference_data))
        _names = [Path(file["location"]).name for file in file_info[1:]]
        if len(absorbance_data) > 0:
            layout = self._format_UV_Vis_plot(absorbance_data, names=_names)
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
