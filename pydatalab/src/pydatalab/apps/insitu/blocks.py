import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bokeh.embed
import numpy as np
import pandas as pd
from bokeh.events import DoubleTap
from bokeh.layouts import gridplot
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    CrosshairTool,
    CustomJS,
    HoverTool,
    LinearColorMapper,
    Range1d,
    TapTool,
)
from bokeh.plotting import figure
from datalab_app_plugin_nmr_insitu import process_datalab_data

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class InsituBlock(DataBlock):
    blocktype = "insitu"
    name = "NMR insitu"
    description = "A simple NMR insitu block from .zip files."
    accepted_file_extensions = (".zip",)
    available_folders: List[str] = []
    nmr_folder_name = ""
    echem_folder_name = ""
    folder_name = ""

    defaults = {
        "ppm1": 0.0,
        "ppm2": 0.0,
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

    def get_available_folders(self) -> List[str]:
        """
        Extract and return a list of available folders from the zip file.

        This method opens the zip file identified by file_id, extracts the main folder
        and its subfolders, and returns a sorted list of subfolder names.

        Returns:
            List[str]: Sorted list of subfolder names, or empty list if file not found or on error.
        """
        if "file_id" not in self.data:
            LOGGER.warning("No file_id in data")
            return []

        main_folder = self.data.get("folder_name")
        LOGGER.info(f"Main folder name: {main_folder}")

        if not main_folder:
            LOGGER.warning("Main folder name not specified")
            return []

        try:
            file_info = get_file_info_by_id(self.data["file_id"])
            file_path = file_info.get("location")
            LOGGER.info(f"File path: {file_path}")

            if not file_path or not os.path.exists(file_path):
                LOGGER.warning(f"File not found: {file_path}")
                return []

            folders = set()
            with zipfile.ZipFile(file_path, "r") as zip_folder:
                main_folder = zip_folder.namelist()[0].split("/")[0]

                for file in zip_folder.namelist():
                    if file.startswith(main_folder + "/"):
                        sub_path = file[len(main_folder) + 1 :]
                        sub_folder = sub_path.split("/")[0] if "/" in sub_path else None
                        if sub_folder:
                            folders.add(sub_folder)

            folder_list = sorted(list(folders))
            LOGGER.info(f"Found folders in '{main_folder}': {folder_list}")

            return folder_list
        except Exception as e:
            LOGGER.error(f"Error getting folders from zip file: {str(e)}")
            import traceback

            LOGGER.error(traceback.format_exc())
            return []

    def process_and_store_data(self) -> bool:
        """
        Process insitu NMR and electrochemical data and store results.

        This method validates input parameters, extracts data from the specified folders,
        and stores the processed data in the block's data attribute.

        Returns:
            bool: True if processing was successful, False otherwise.
        """
        folders = self.get_available_folders()
        self.data["available_folders"] = folders

        nmr_folder_name = self.data.get("nmr_folder_name")
        echem_folder_name = self.data.get("echem_folder_name")

        if not nmr_folder_name or not echem_folder_name:
            self.data["warnings"] = ["Both NMR and Echem folder names must be specified"]
            return False

        try:
            item_id = self.data.get("item_id")
            folder_name = self.data.get("folder_name")
            nmr_folder_name = self.data.get("nmr_folder_name")
            echem_folder_name = self.data.get("echem_folder_name")

            if not all([nmr_folder_name, echem_folder_name]):
                self.data["warnings"] = ["Both NMR and Echem folder names are required"]
                return False

            start_exp = int(self.data.get("start_exp", self.defaults["start_exp"]))
            exclude_exp = self.data.get("exclude_exp", self.defaults["exclude_exp"])

            api_url = os.environ.get("DATALAB_API_URL")
            if not api_url:
                LOGGER.warning(
                    "API URL is missing. Please set the 'DATALAB_API_URL' environment variable."
                )
                self.data["errors"] = [
                    "API URL is missing. Please set the 'DATALAB_API_URL' environment variable."
                ]
                return False

            try:
                result = process_datalab_data(
                    api_url=api_url,
                    item_id=item_id,
                    folder_name=folder_name,
                    nmr_folder_name=nmr_folder_name,
                    echem_folder_name=echem_folder_name,
                    start_at=start_exp,
                    exclude_exp=exclude_exp,
                )

            except FileNotFoundError as e:
                LOGGER.warning(f"Folder not found: {str(e)}")
                self.data["errors"] = [f"Folder not found: {str(e)}"]
                return False

            except Exception as e:
                LOGGER.warning(f"Error processing data: {str(e)}")
                self.data["errors"] = [f"Error processing data: {str(e)}"]
                return False

            self.data.pop("warnings", None)
            self.data.pop("errors", None)

            nmr_data = result["nmr_spectra"]
            ppm_values = np.array(nmr_data.get("ppm", []))

            ppm1 = self.data["ppm1"] = min(ppm_values)
            ppm2 = self.data["ppm2"] = max(ppm_values)

            self.data.update(
                {
                    "nmr_data": result["nmr_spectra"],
                    "echem_data": result.get("echem", {}),
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
        """
        Determine if data needs to be reprocessed based on parameter changes.
        PPM changes should not trigger reprocessing.
        """
        if "processing_params" not in self.data or "nmr_data" not in self.data:
            return True

        params = self.data["processing_params"]
        current_params = {
            "file_id": self.data.get("file_id"),
            "start_exp": int(self.data.get("start_exp", self.defaults["start_exp"])),
            "exclude_exp": self.data.get("exclude_exp", self.defaults["exclude_exp"]),
        }

        for key in current_params:
            if params.get(key) != current_params[key]:
                LOGGER.info(f"Parameter {key} changed, reprocessing data...")
                return True

        return False

    def generate_insitu_nmr_plot(self) -> Tuple[pd.DataFrame, List[str]]:
        """
        Generate combined NMR and electrochemical plots using the operando-style layout.

        This method coordinates the creation of various plot components and combines
        them into a unified visualization.

        Returns:
            Tuple[pd.DataFrame, List[str]]: Time data and status messages.
        """
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

            needs_reprocessing = self.should_reprocess_data()
            if needs_reprocessing:
                LOGGER.info("Processing new data...")
                if not self.process_and_store_data():
                    return None, []
            else:
                LOGGER.info("Using stored data...")
                self.data["processing_params"]["ppm1"] = float(
                    self.data.get("ppm1", self.defaults["ppm1"])
                )
                self.data["processing_params"]["ppm2"] = float(
                    self.data.get("ppm2", self.defaults["ppm2"])
                )

            plot_data = self._prepare_plot_data()
            if not plot_data:
                return None, []

            shared_ranges = self._create_shared_ranges(plot_data)

            heatmap_figure = self._create_heatmap_figure(plot_data, shared_ranges)
            nmrplot_figure = self._create_nmr_line_figure(plot_data, shared_ranges)
            echemplot_figure = self._create_echem_figure(plot_data, shared_ranges)

            heatmap_figure.js_on_event(
                DoubleTap, CustomJS(args=dict(p=heatmap_figure), code="p.reset.emit()")
            )
            nmrplot_figure.js_on_event(
                DoubleTap, CustomJS(args=dict(p=nmrplot_figure), code="p.reset.emit()")
            )
            echemplot_figure.js_on_event(
                DoubleTap, CustomJS(args=dict(p=echemplot_figure), code="p.reset.emit()")
            )

            self._link_plots(heatmap_figure, nmrplot_figure, echemplot_figure, plot_data)

            grid = [[None, nmrplot_figure], [echemplot_figure, heatmap_figure]]
            gp = gridplot(grid, merge_tools=True)

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(gp, theme=DATALAB_BOKEH_THEME)

            return self.data.get("time_data"), ["Plot successfully generated"]

        except Exception as e:
            import traceback

            LOGGER.error(f"Error in generate_insitu_nmr_plot: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return None, []

    def _prepare_plot_data(self) -> Optional[Dict[str, Any]]:
        """
        Extract and prepare data for plotting.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing prepared plot data,
                                      or None if data extraction fails.
        """
        try:
            nmr_data = self.data["nmr_data"]
            echem_data = self.data["echem_data"]
            metadata = self.data["metadata"]

            ppm_values = np.array(nmr_data.get("ppm", []))
            if len(ppm_values) == 0:
                LOGGER.error("No PPM values found in NMR data")
                return None

            spectra = nmr_data.get("spectra", [])
            if not spectra:
                LOGGER.error("No spectra found in NMR data")
                return None

            try:
                spectra_intensities = [
                    np.array(spectrum["intensity"]).tolist() for spectrum in spectra
                ]

                intensity_matrix = np.array(
                    [np.array(spectrum["intensity"]) for spectrum in spectra]
                )

            except Exception as e:
                LOGGER.error(f"Error processing spectrum intensities: {e}")
                LOGGER.error(f"Spectrum data structure: {spectra[0] if spectra else 'No spectra'}")
                return None

            time_range = metadata["time_range"]
            first_spectrum_intensities = np.array(spectra[0]["intensity"])

            intensity_min = np.min(intensity_matrix)
            intensity_max = np.max(intensity_matrix)

            return {
                "ppm_values": ppm_values,
                "spectra": spectra,
                "spectra_intensities": spectra_intensities,
                "intensity_matrix": intensity_matrix,
                "time_range": time_range,
                "first_spectrum_intensities": first_spectrum_intensities,
                "intensity_min": intensity_min,
                "intensity_max": intensity_max,
                "echem_data": echem_data,
            }

        except Exception as e:
            LOGGER.error(f"Error preparing plot data: {str(e)}")
            return None

    def _create_shared_ranges(self, plot_data: Dict[str, Any]) -> Dict[str, Range1d]:
        """
        Create shared range objects for linking multiple plots.

        Args:
            plot_data: Dictionary containing prepared plot data

        Returns:
            Dict[str, Range1d]: Dictionary of shared range objects
        """
        ppm_values = plot_data["ppm_values"]
        time_range = plot_data["time_range"]
        intensity_min = np.min(plot_data["intensity_matrix"])
        intensity_max = np.max(plot_data["intensity_matrix"])

        shared_y_range = Range1d(start=time_range["start"], end=time_range["end"])

        ppm1 = float(self.data.get("ppm1", self.defaults["ppm1"]))
        ppm2 = float(self.data.get("ppm2", self.defaults["ppm2"]))

        ppm_min = min(ppm_values)
        ppm_max = max(ppm_values)

        ppm1 = max(min(ppm1, ppm_max), ppm_min)
        ppm2 = max(min(ppm2, ppm_max), ppm_min)

        shared_x_range = Range1d(start=max(ppm1, ppm2), end=min(ppm1, ppm2))

        intensity_range = Range1d(start=intensity_min, end=intensity_max)

        return {
            "shared_y_range": shared_y_range,
            "shared_x_range": shared_x_range,
            "intensity_range": intensity_range,
        }

    def _create_heatmap_figure(
        self, plot_data: Dict[str, Any], ranges: Dict[str, Range1d]
    ) -> figure:
        """
        Create the heatmap figure component.

        Args:
            plot_data: Dictionary containing prepared plot data
            ranges: Dictionary of shared range objects

        Returns:
            figure: Configured Bokeh heatmap figure
        """
        ppm_values = plot_data["ppm_values"]
        intensity_matrix = plot_data["intensity_matrix"]
        time_range = plot_data["time_range"]
        intensity_min = plot_data["intensity_min"]
        intensity_max = plot_data["intensity_max"]

        tools = "pan,wheel_zoom,box_zoom,reset,save"

        heatmap_figure = figure(
            x_axis_label="δ (ppm)",
            y_axis_label="t (h)",
            x_range=ranges["shared_x_range"],
            y_range=ranges["shared_y_range"],
            height=400,
            tools=tools,
        )

        color_mapper = LinearColorMapper(palette="Turbo256", low=intensity_min, high=intensity_max)

        heatmap_figure.image(
            image=[intensity_matrix],
            x=max(ppm_values),
            y=time_range["start"],
            dw=abs(max(ppm_values) - min(ppm_values)),
            dh=time_range["end"] - time_range["start"],
            color_mapper=color_mapper,
            level="image",
        )

        time_points = len(intensity_matrix)
        if time_points > 0:
            times = np.linspace(time_range["start"], time_range["end"], time_points)
            experiment_numbers = np.arange(1, time_points + 1)

            source = ColumnDataSource(
                data={
                    "x": [(max(ppm_values) + min(ppm_values)) / 2] * time_points,
                    "y": times,
                    "width": [abs(max(ppm_values) - min(ppm_values))] * time_points,
                    "height": [(time_range["end"] - time_range["start"]) / time_points]
                    * time_points,
                    "exp_num": experiment_numbers,
                }
            )

            rects = heatmap_figure.rect(
                x="x",
                y="y",
                width="width",
                height="height",
                source=source,
                fill_alpha=0,
                line_alpha=0,
            )

            hover_tool = HoverTool(
                renderers=[rects],
                tooltips=[("Exp.", "@exp_num")],
                mode="mouse",
                point_policy="follow_mouse",
            )

            heatmap_figure.add_tools(hover_tool)

            plot_data["heatmap_source"] = source

        heatmap_figure.grid.grid_line_width = 0
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12)
        heatmap_figure.add_layout(color_bar, "right")

        return heatmap_figure

    def _create_nmr_line_figure(
        self, plot_data: Dict[str, Any], ranges: Dict[str, Range1d]
    ) -> figure:
        """
        Create the NMR line plot figure component.

        Args:
            plot_data: Dictionary containing prepared plot data
            ranges: Dictionary of shared range objects

        Returns:
            figure: Configured Bokeh line figure with data source
        """
        ppm_values = plot_data["ppm_values"]
        first_spectrum_intensities = plot_data["first_spectrum_intensities"]

        tools = "pan,wheel_zoom,box_zoom,reset,save"

        ppm_list = ppm_values.tolist() if isinstance(ppm_values, np.ndarray) else ppm_values
        intensity_list = (
            first_spectrum_intensities.tolist()
            if isinstance(first_spectrum_intensities, np.ndarray)
            else first_spectrum_intensities
        )

        line_source = ColumnDataSource(
            data={
                "δ (ppm)": ppm_list,
                "intensity": intensity_list,
            }
        )

        clicked_spectra_source = ColumnDataSource(
            data={"δ (ppm)": [], "intensity": [], "exp_index": [], "color": []}
        )

        nmrplot_figure = figure(
            y_axis_label="intensity",
            aspect_ratio=2,
            x_range=ranges["shared_x_range"],
            y_range=ranges["intensity_range"],
            tools=tools,
        )

        nmrplot_figure.line(
            x="δ (ppm)",
            y="intensity",
            source=line_source,
            line_width=1,
            color="blue",
            legend_label="Reference",
        )

        nmrplot_figure.multi_line(
            xs="δ (ppm)",
            ys="intensity",
            source=clicked_spectra_source,
            line_color="color",
            line_width=1,
            legend_field="exp_index",
        )

        nmrplot_figure.legend.click_policy = "hide"
        nmrplot_figure.legend.location = "top_right"

        plot_data["line_source"] = line_source
        plot_data["clicked_spectra_source"] = clicked_spectra_source
        return nmrplot_figure

    def _create_echem_figure(self, plot_data: Dict[str, Any], ranges: Dict[str, Range1d]) -> figure:
        """
        Create the electrochemical data figure component.

        Args:
            plot_data: Dictionary containing prepared plot data
            ranges: Dictionary of shared range objects

        Returns:
            figure: Configured Bokeh electrochemical figure
        """
        echem_data = plot_data["echem_data"]

        tools = "pan,wheel_zoom,box_zoom,reset,save"

        echemplot_figure = figure(
            x_axis_label="voltage (V)",
            y_axis_label="t (h)",
            y_range=ranges["shared_y_range"],
            height=400,
            width=250,
            tools=tools,
        )

        if echem_data and "Voltage" in echem_data and "time" in echem_data:
            times = np.array(echem_data["time"])
            voltages = np.array(echem_data["Voltage"])

            time_range = plot_data["time_range"]
            time_span = time_range["end"] - time_range["start"]
            exp_count = len(plot_data["spectra"])

            exp_numbers = np.floor(((times - time_range["start"]) / time_span) * exp_count) + 1
            exp_numbers = np.clip(exp_numbers, 1, exp_count)

            echem_source = ColumnDataSource(
                data={"time": times, "voltage": voltages, "exp_num": exp_numbers}
            )

            echemplot_figure.line(
                x="voltage",
                y="time",
                source=echem_source,
            )

            hover_tool = HoverTool(
                tooltips=[
                    ("Exp.", "@exp_num{0}"),
                    ("Time (h)", "@time{0.00}"),
                    ("Voltage (V)", "@voltage{0.000}"),
                ],
                mode="mouse",
                point_policy="follow_mouse",
            )

            echemplot_figure.add_tools(hover_tool)

        return echemplot_figure

    def _link_plots(
        self,
        heatmap_figure: figure,
        nmrplot_figure: figure,
        echemplot_figure: figure,
        plot_data: Dict[str, Any],
    ) -> None:
        """
        Link the plots together with interactive tools and callbacks.

        Args:
            heatmap_figure: The heatmap figure component
            nmrplot_figure: The NMR line plot figure component
            echemplot_figure: The electrochemical figure component
            plot_data: Dictionary containing prepared plot data
        """
        line_source = plot_data["line_source"]
        clicked_spectra_source = plot_data["clicked_spectra_source"]
        spectra_intensities = plot_data["spectra_intensities"]
        ppm_values = plot_data["ppm_values"]
        intensity_matrix = plot_data["intensity_matrix"]
        heatmap_source = plot_data.get("heatmap_source")

        colors = [
            "red",
            "green",
            "orange",
            "purple",
            "brown",
            "darkblue",
            "teal",
            "magenta",
            "olive",
            "navy",
        ]

        crosshair = CrosshairTool(dimensions="width", line_color="grey")
        heatmap_figure.add_tools(crosshair)
        echemplot_figure.add_tools(crosshair)

        hover = next((tool for tool in heatmap_figure.tools if isinstance(tool, HoverTool)), None)
        if hover:
            hover.callback = CustomJS(
                args=dict(
                    line_source=line_source,
                    spectra_intensities=spectra_intensities,
                    ppm_values=ppm_values.tolist(),
                    heatmap_source=heatmap_source,
                ),
                code="""
                        const geometry = cb_data['geometry'];

                        let closestIndex = 0;
                        let minDistance = Infinity;
                        for (let i = 0; i < heatmap_source.data.y.length; i++) {
                            const distance = Math.abs(heatmap_source.data.y[i] - geometry.y);
                            if (distance < minDistance) {
                                minDistance = distance;
                                closestIndex = i;
                            }
                        }

                        const exp_num = heatmap_source.data.exp_num[closestIndex];

                        const index = exp_num - 1;

                        var data = line_source.data;
                        data['intensity'] = spectra_intensities[index];
                        line_source.change.emit();
                    """,
            )

        if heatmap_source:
            tap_tool = TapTool()
            heatmap_figure.add_tools(tap_tool)
            tap_callback = CustomJS(
                args=dict(
                    heatmap_source=heatmap_source,
                    clicked_spectra_source=clicked_spectra_source,
                    spectra_intensities=spectra_intensities,
                    ppm_values=ppm_values.tolist(),
                    colors=colors,
                ),
                code="""
                        const indices = cb_obj.indices;
                        if (indices.length === 0) return;

                        const index = indices[0];
                        const exp_num = heatmap_source.data.exp_num[index];

                        const existing_indices = clicked_spectra_source.data.exp_index;
                        if (existing_indices.includes(exp_num)) return;

                        const color_index = existing_indices.length % colors.length;

                        const new_xs = [...clicked_spectra_source.data['δ (ppm)']];
                        const new_ys = [...clicked_spectra_source.data.intensity];
                        const new_indices = [...clicked_spectra_source.data.exp_index];
                        const new_colors = [...clicked_spectra_source.data.color];

                        new_xs.push(ppm_values);
                        new_ys.push(spectra_intensities[index]);
                        new_indices.push(exp_num);
                        new_colors.push(colors[color_index]);

                        clicked_spectra_source.data = {
                            'δ (ppm)': new_xs,
                            'intensity': new_ys,
                            'exp_index': new_indices,
                            'color': new_colors
                        };

                        clicked_spectra_source.change.emit();
                    """,
            )

            heatmap_source.selected.js_on_change("indices", tap_callback)

        heatmap_figure.x_range.js_on_change(
            "start",
            CustomJS(
                args=dict(
                    color_mapper=heatmap_figure.select_one(LinearColorMapper),
                    intensity_matrix=intensity_matrix.tolist(),
                    ppm_array=ppm_values.tolist(),
                    global_min=np.min(intensity_matrix),
                    global_max=np.max(intensity_matrix),
                ),
                code="""
                        const start_index = ppm_array.findIndex(ppm => ppm <= cb_obj.end);
                        const end_index = ppm_array.findIndex(ppm => ppm <= cb_obj.start);

                        if (start_index < 0 || end_index < 0 || start_index >= ppm_array.length || end_index >= ppm_array.length) {
                            color_mapper.low = global_min;
                            color_mapper.high = global_max;
                            return;
                        }

                        if (Math.abs(end_index - start_index) < 5) {
                            return;
                        }

                        let min_intensity = Infinity;
                        let max_intensity = -Infinity;

                        for (let i = 0; i < intensity_matrix.length; i++) {
                            for (let j = Math.min(start_index, end_index); j <= Math.max(start_index, end_index); j++) {
                                if (j >= 0 && j < intensity_matrix[i].length) {
                                    const value = intensity_matrix[i][j];
                                    min_intensity = Math.min(min_intensity, value);
                                    max_intensity = Math.max(max_intensity, value);
                                }
                            }
                        }

                        if (Math.abs(max_intensity - min_intensity) < 0.1 * Math.abs(global_max - global_min)) {
                            const padding = 0.1 * Math.abs(global_max - global_min);
                            min_intensity = Math.max(min_intensity - padding, global_min);
                            max_intensity = Math.min(max_intensity + padding, global_max);
                        }

                        color_mapper.low = min_intensity;
                        color_mapper.high = max_intensity;
                    """,
            ),
        )

        heatmap_figure.x_range.tags = [ppm_values.tolist(), intensity_matrix.tolist()]

        line_y_range = nmrplot_figure.y_range
        line_y_range.js_link("start", heatmap_figure.select_one(LinearColorMapper), "low")
        line_y_range.js_link("end", heatmap_figure.select_one(LinearColorMapper), "high")

        tap_tool = TapTool()

        nmrplot_figure.add_tools(tap_tool)

        remove_line_callback = CustomJS(
            args=dict(clicked_spectra_source=clicked_spectra_source),
            code="""
            const indices = clicked_spectra_source.selected.indices;
            if (indices.length === 0) return;

            let data = clicked_spectra_source.data;

            for (let i = indices.length - 1; i >= 0; i--) {
                let index = indices[i];
                data['δ (ppm)'].splice(index, 1);
                data['intensity'].splice(index, 1);
                data['exp_index'].splice(index, 1);
                data['color'].splice(index, 1);
            }

            clicked_spectra_source.change.emit();
        """,
        )

        clicked_spectra_source.selected.js_on_change("indices", remove_line_callback)
