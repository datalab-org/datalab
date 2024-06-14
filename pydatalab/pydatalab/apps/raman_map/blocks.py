import os
from pathlib import Path

import bokeh
import numpy as np
import PIL
from bokeh.layouts import column
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from pybaselines import Baseline
from rsciio.renishaw import file_reader

from pydatalab.blocks.base import DataBlock
from pydatalab.file_utils import get_file_info_by_id


class RamanMapBlock(DataBlock):
    blocktype = "raman_map"
    description = "Raman spectroscopy map"
    accepted_file_extensions = ".wdf"

    @property
    def plot_functions(self):
        return (self.generate_raman_map_plot,)

    @classmethod
    def get_map_data(self, location: Path | str):
        """Read the .wdf file with RosettaSciIO and extract relevant
        data.

        Parameters:
            location: The location of the file to read.

        Returns:
            col: list of numbers corresponding to colors of each scatter
            point
            p: plot of image and points Raman was measured
            metadata: metadata associated witht the measurement


        """

        raman_data = file_reader(location)

        if len(raman_data[0]["axes"]) == 3:
            pass
        elif len(raman_data[0]["axes"]) == 1:
            raise RuntimeError("This block is for 2D Raman data, not 1D")
        else:
            raise RuntimeError("Data is not compatible 1D or 2D Raman data.")

        for dictionary in raman_data[0]["axes"]:
            if dictionary["name"] == "Raman Shift":
                raman_shift = []
                for i in range(int(dictionary["size"])):
                    raman_shift.append(float(dictionary["offset"]) + float(dictionary["scale"]) * i)
        return np.array(raman_shift), raman_data[0]["data"], raman_data[0]["metadata"]

    def plot_raman_map(self, location: str | Path):
        data = file_reader(location)
        raman_shift, intensity_data, metadata = self.get_map_data(location)
        x_coordinates = []
        # gets the size, point spacing and original offset of x-axis
        # check for origin
        size_x = data[0]["original_metadata"]["WMAP_0"]["size_xyz"][0]
        scale_x = data[0]["original_metadata"]["WMAP_0"]["scale_xyz"][0]
        offset_x = data[0]["original_metadata"]["WMAP_0"]["offset_xyz"][0]
        # generates x-coordinates
        for i in range(size_x):
            x_coordinates.append(i * scale_x + offset_x)
        y_coordinates = []
        # gets the size, point spacing and original offset of x-axis
        size_y = data[0]["original_metadata"]["WMAP_0"]["size_xyz"][1]
        scale_y = data[0]["original_metadata"]["WMAP_0"]["scale_xyz"][1]
        offset_y = data[0]["original_metadata"]["WMAP_0"]["offset_xyz"][1]
        # generates y-coordinates
        for i in range(size_y):
            y_coordinates.append(i * scale_y + offset_y)

        coordinate_pairs = []
        for y in y_coordinates:
            for x in x_coordinates:
                coordinate_pairs.append((x, y))

        # extracts image and gets relevant data
        image_data = data[0]["original_metadata"]["WHTL_0"]["image"]
        image = PIL.Image.open(image_data)
        origin = data[0]["original_metadata"]["WHTL_0"]["FocalPlaneXYOrigins"]
        origin = [float(origin[0]), float(origin[1])]
        x_span = float(data[0]["original_metadata"]["WHTL_0"]["FocalPlaneXResolution"])
        y_span = float(data[0]["original_metadata"]["WHTL_0"]["FocalPlaneYResolution"])
        # converts image to vector compatible with bokeh
        image_array = np.array(image, dtype=np.uint8)
        image_array = np.flip(image_array, axis=0)
        image_array = np.dstack((image_array, 255 * np.ones_like(image_array[:, :, 0])))
        img_vector = image_array.view(dtype=np.uint32).reshape(
            (image_array.shape[0], image_array.shape[1])
             )
        # generates numbers for colours for points in linear gradient
        col = [
            i / (len(x_coordinates) * len(y_coordinates))
            for i in range(len(x_coordinates) * len(y_coordinates))
        ]

        # links x- and y-coordinates with colour numbers
        source = ColumnDataSource(
            data={
                "x": [pair[0] for pair in coordinate_pairs],
                "y": [pair[1] for pair in coordinate_pairs],
                "col": col,
            }
        )
        # gemerates colormap for coloured scatter poitns
        exp_cmap = LinearColorMapper(palette="Turbo256", low=min(col), high=max(col))

        # generates image figure and plots image
        from pathlib import Path

        p = bokeh.plotting.figure(
            width=image_array.shape[1],
            height=image_array.shape[0],
            x_range=(origin[0], origin[0] + x_span),
            y_range=(origin[1] + y_span, origin[1]),
        )
        p.image_rgba(image=[img_vector], x=origin[0], y=origin[1], dw=x_span, dh=y_span)
        p = bokeh.plotting.figure(
            width=image_data.shape[1],
            height=image_data.shape[0],
            x_range=(origin[0], origin[0] + x_span),
            y_range=(origin[1] + y_span, origin[1]),
        )
        p.image_rgba(image=[img_vector], x=origin[0], y=origin[1] + y_span, dw=x_span, dh=y_span)
        # plot scatter points and colorbar
        p.circle("x", "y", size=10, source=source, color={"field": "col", "transform": exp_cmap})
        color_bar = ColorBar(
            color_mapper=exp_cmap, label_standoff=12, border_line_color=None, location=(0, 0)
        )
        p.add_layout(color_bar, "right")
        bokeh.plotting.save(p)
        # return color numbers to use in spectra plotting and returns figure object

        bokeh.plotting.output_file(Path(__file__).parent / "plot.html")
        return col, p, metadata

    def plot_raman_spectra(self, location: str | Path, col):
        """Read the .wdf file with RosettaSciIO and extract relevant
        data.

        Parameters:
            location: The location of the file to read.
            col: list of numbers corresponding to colors of the points generated
            in the map plot

        Returns:
            Bokeh plot of the Raman spectra


        """
        # generates plot and extracts raman spectra from .wdf file
        p = bokeh.plotting.figure(
            width=800,
            height=400,
            x_axis_label="Raman Shift (cm-1)",
            y_axis_label="Intensity (a.u.)",
        )
        raman_shift, intensity_data, metadata = self.get_map_data(location)
        intensity_list = []

        # generates baseline to be subtracted from spectra
        def generate_baseline(x_data, y_data):
            baseline_fitter = Baseline(x_data=x_data)
            baseline = baseline_fitter.mor(y_data, half_window=30)[0]
            return baseline

        # the bokeh ColumnDataSource works was easiest for me to work with this as a list so making list of spectra intensities
        for i in range(intensity_data.shape[0]):
            for j in range(intensity_data.shape[1]):
                intensity_spectrum = intensity_data[i, j, :]
                # want to make optional but will leave for now
                baseline = generate_baseline(raman_shift, intensity_spectrum)
                intensity_spectrum = intensity_spectrum - baseline
                intensity_list.append(intensity_spectrum)

        # generates colorbar
        source = ColumnDataSource(
            data={"x": [raman_shift] * len(intensity_list), "y": intensity_list, "col": col}
        )
        exp_cmap = LinearColorMapper(palette="Turbo256", low=min(col), high=max(col))
        # plots spectra
        p.multi_line(
            "x", "y", line_width=0.5, source=source, color={"field": "col", "transform": exp_cmap}
        )
        return p

    def generate_raman_map_plot(self):
        file_info = None
        pattern_dfs = None

        if "file_id" not in self.data:
            return None

        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                raise RuntimeError(
                    "RamanBlock.generate_raman_plot(): Unsupported file extension (must be one of %s), not %s",
                    self.accepted_file_extensions,
                    ext,
                )
        col, p1, metadata = self.plot_raman_map(file_info["location"])
        p2 = self.plot_raman_spectra(file_info["location"], col=col)
        self.data["bokeh_plot_data"] = bokeh.embed.json_item(column(p1, p2))
