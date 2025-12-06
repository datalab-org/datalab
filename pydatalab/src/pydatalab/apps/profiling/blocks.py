"""
Profiling data blocks for surface profilometry visualization.
"""

import warnings
from pathlib import Path

import bokeh.embed
import numpy as np
from bokeh.layouts import column
from bokeh.models import ColorBar, LinearColorMapper
from bokeh.plotting import figure

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME
from pydatalab.file_utils import get_file_info_by_id

from .wyko_reader import load_wyko_asc


class ProfilingBlock(DataBlock):
    """Block for visualizing surface profilometry data."""

    accepted_file_extensions: tuple[str, ...] = (".asc",)
    blocktype = "profiling"
    name = "Surface Profiling"
    description = "This block can plot surface profilometry data from Wyko .ASC files"

    @property
    def plot_functions(self):
        return (self.generate_profiling_plot,)

    @staticmethod
    def _create_image_plot(
        image_data: np.ndarray,
        pixel_size: float | None = None,
        title: str = "Surface Profile",
        colorbar_label: str = "Height",
    ):
        """
        Create a 2D Bokeh image plot for surface profilometry data.

        Args:
            image_data: 2D numpy array of height/intensity values
            pixel_size: Physical pixel size in mm (for axis scaling)
            title: Plot title
            colorbar_label: Label for the colorbar

        Returns:
            Bokeh figure with image plot
        """
        # Get dimensions
        n_rows, n_cols = image_data.shape

        # Calculate physical dimensions if pixel_size is available
        # pixel_size is in mm, convert to µm for display
        if pixel_size:
            pixel_size_um = pixel_size * 1000  # mm to µm
            x_range = (0, n_cols * pixel_size_um)
            y_range = (0, n_rows * pixel_size_um)
            x_label = "X (µm)"
            y_label = "Y (µm)"
        else:
            x_range = (0, n_cols)
            y_range = (0, n_rows)
            x_label = "X (pixels)"
            y_label = "Y (pixels)"

        # Calculate color range, ignoring NaN values
        valid_data = image_data[~np.isnan(image_data)]
        if len(valid_data) > 0:
            # Use percentiles to avoid outliers dominating the color scale
            vmin = np.percentile(valid_data, 1)
            vmax = np.percentile(valid_data, 99)
        else:
            vmin, vmax = 0, 1

        # Create color mapper
        color_mapper = LinearColorMapper(
            palette="Viridis256", low=vmin, high=vmax, nan_color="white"
        )

        # Create figure
        p = figure(
            title=title,
            x_axis_label=x_label,
            y_axis_label=y_label,
            x_range=x_range,
            y_range=y_range,
            tools="pan,wheel_zoom,box_zoom,reset,save",
            sizing_mode="scale_width",
            aspect_ratio=n_cols / n_rows,
            match_aspect=True,
        )

        # Add image
        # Note: bokeh.plotting.figure.image expects data as [image] where image is 2D array
        # dw and dh are the width and height in data coordinates
        p.image(
            image=[image_data],
            x=0,
            y=0,
            dw=x_range[1],
            dh=y_range[1],
            color_mapper=color_mapper,
        )

        # Add colorbar
        color_bar = ColorBar(
            color_mapper=color_mapper,
            title=colorbar_label,
            location=(0, 0),
        )
        p.add_layout(color_bar, "right")

        # Style
        p.toolbar.logo = "grey"
        p.grid.visible = False

        return p

    @staticmethod
    def _create_histogram_plot(
        image_data: np.ndarray,
        title: str = "Height Distribution",
        x_label: str = "Height",
        n_bins: int = 100,
    ):
        """
        Create a histogram plot for z-values (height distribution).

        Args:
            image_data: 2D numpy array of height/intensity values
            title: Plot title
            x_label: Label for x-axis
            n_bins: Number of bins for the histogram

        Returns:
            Bokeh figure with histogram plot
        """
        # Get valid (non-NaN) data
        valid_data = image_data[~np.isnan(image_data)]

        if len(valid_data) == 0:
            # Create empty plot if no valid data
            p = figure(
                title=title,
                x_axis_label=x_label,
                y_axis_label="Count",
                sizing_mode="scale_width",
                height=300,
            )
            return p

        # Compute histogram
        hist, edges = np.histogram(valid_data, bins=n_bins)

        # Create figure
        p = figure(
            title=title,
            x_axis_label=x_label,
            y_axis_label="Count",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            sizing_mode="scale_width",
            height=300,
        )

        # Plot histogram as quads
        p.quad(
            top=hist,
            bottom=0,
            left=edges[:-1],
            right=edges[1:],
            fill_color="navy",
            line_color="white",
            alpha=0.7,
        )

        # Style
        p.toolbar.logo = "grey"

        return p

    def generate_profiling_plot(self, filepath=None):
        """Generate the profiling plot from the associated file.

        Args:
            filepath: Optional path to the file to plot. If not provided,
                     uses the file_id from self.data to look up the file.
        """
        # Get file path either from parameter or from database lookup
        if filepath is not None:
            file_path = Path(filepath)
        else:
            if "file_id" not in self.data:
                return
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            file_path = Path(file_info["location"])

        ext = file_path.suffix.lower()

        if ext not in self.accepted_file_extensions:
            warnings.warn(
                f"Unsupported file extension (must be one of {self.accepted_file_extensions}, not {ext})"
            )
            return

        try:
            # Load the Wyko ASC file
            result = load_wyko_asc(file_path, load_intensity=False, progress=False)

            # Get the height data
            height_data = result["raw_data"]
            pixel_size = result["metadata"].get("pixel_size")

            # Create the 2D image plot
            image_plot = self._create_image_plot(
                height_data,
                pixel_size=pixel_size,
                title="Surface Height Profile",
                colorbar_label="Height",
            )

            # Create the histogram plot
            histogram_plot = self._create_histogram_plot(
                height_data,
                title="Height Distribution",
                x_label="Height (µm)",
                n_bins=100,
            )

            # Combine plots in a vertical layout
            layout = column(image_plot, histogram_plot, sizing_mode="scale_width")

            # Store as bokeh JSON
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)

        except Exception as e:
            warnings.warn(f"Error loading profiling data: {e}")
            return
