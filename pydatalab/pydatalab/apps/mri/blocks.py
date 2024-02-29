import bokeh
import numpy as np

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME
from pydatalab.file_utils import get_file_info_by_id


class MRIBlock(DataBlock):
    blocktype = "mri"
    description = "In situ MRI"
    accepted_file_extensions = ("2dseq",)

    @property
    def plot_functions(self):
        return (self.generate_mri_plot,)

    @classmethod
    def load_2dseq(
        cls,
        location: str,
        image_size: tuple[int, int] = (512, 512),
    ) -> list[np.ndarray]:
        if not isinstance(location, str):
            location = str(location)

        arrays = []
        with open(location, "rb") as f:
            while data := f.read():
                arr = np.frombuffer(data, dtype=np.dtype("<u2"))
                arrays.append(arr)

        image_arrays = []
        for arr in arrays:
            image_pixels = image_size[0] * image_size[1]
            num_images = arr.shape[0] // image_pixels
            for i in range(num_images):
                # grab an image_size square slice from arrays
                image_arrays.append(
                    arr[i * image_pixels : (i + 1) * image_pixels].reshape(*image_size).copy()
                )

        return image_arrays

    def generate_mri_plot(self):
        """Generate image plots of MRI data."""
        from bokeh.layouts import column
        from bokeh.models import ColorBar, ColumnDataSource, CustomJS, Slider
        from bokeh.plotting import figure

        if "file_id" not in self.data:
            return None
        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

        image_array = self.load_2dseq(
            file_info["location"],
        )

        if len(image_array) == 0:
            raise RuntimeError(f"Could not find any MRI images in file {file_info['name']!r}")

        p = figure(
            sizing_mode="scale_width",
            aspect_ratio=1,
            x_axis_label="",
            y_axis_label="",
        )

        image_source = ColumnDataSource(data={"image": [image_array[0]]})

        cmap = bokeh.palettes.Viridis256
        color_mapper = bokeh.models.LogColorMapper(palette=cmap, low=1, high=np.max(image_array))

        p.image(
            image="image",
            source=image_source,
            x=0,
            y=0,
            dw=10,
            dh=10,
            color_mapper=color_mapper,
        )

        p.axis.visible = False
        p.xgrid.visible = False
        p.ygrid.visible = False

        # Set limits to edge of images defined by 10x10
        p.x_range.start = 0
        p.x_range.end = 10
        p.y_range.start = 0
        p.y_range.end = 10

        color_bar = ColorBar(color_mapper=color_mapper)

        slider = Slider(
            start=0,
            end=len(image_array) - 1,
            step=1,
            value=0,
            title=f"Select image ({len(image_array)} images)",
        )

        slider_callback = CustomJS(
            args=dict(image_source=image_source, image_array=image_array, slider=slider),
            code="""
var selected_image_index = slider.value;
image_source.data["image"] = [image_array[selected_image_index]];
image_source.change.emit();
""",
        )
        slider.js_on_change("value", slider_callback)

        p.add_layout(color_bar, "right")

        layout = column(slider, p)

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
