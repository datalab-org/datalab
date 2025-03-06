import os
import zipfile
from pathlib import Path
from typing import List, Tuple

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

    def get_available_folders(self) -> List[str]:
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
        """Process insitu NMR and electrochemical data and store results."""
        folders = self.get_available_folders()
        self.data["available_folders"] = folders

        nmr_folder_name = self.data.get("nmr_folder_name")
        echem_folder_name = self.data.get("echem_folder_name")

        if not nmr_folder_name or not echem_folder_name:
            self.data["warnings"] = ["Both NMR and Echem folder names must be specified"]
            return False

        if not self._validate_parameters():
            return False

        try:
            ppm1 = float(self.data.get("ppm1", self.defaults["ppm1"]))
            ppm2 = float(self.data.get("ppm2", self.defaults["ppm2"]))

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

    def generate_insitu_nmr_plot(self) -> Tuple[pd.DataFrame, List[str]]:
        """Generate combined NMR and electrochemical plots using the operando-style layout."""
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

            # ppm1 = self.data["ppm1"]
            # ppm2 = self.data["ppm2"]

            ppm_values = np.array(nmr_data.get("ppm", []))
            if len(ppm_values) == 0:
                LOGGER.error("No PPM values found in NMR data")
                return None, []

            spectra = nmr_data.get("spectra", [])
            if not spectra:
                LOGGER.error("No spectra found in NMR data")
                return None, []

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
                return None, []

            time_range = metadata["time_range"]
            shared_y_range = Range1d(start=time_range["start"], end=time_range["end"])
            shared_x_range = Range1d(start=max(ppm_values), end=min(ppm_values))

            first_spectrum_intensities = np.array(spectra[0]["intensity"])
            line_source = ColumnDataSource(
                data={
                    "δ (ppm)": ppm_values.tolist(),
                    "intensity": first_spectrum_intensities.tolist(),
                }
            )

            # exp_numbers = [
            #     spectrum.get("experiment_number", i + 1) for i, spectrum in enumerate(spectra)
            # ]

            heatmap_figure = figure(
                x_axis_label="δ (ppm)",
                y_axis_label="t (h)",
                x_range=shared_x_range,
                y_range=shared_y_range,
                height=400,
                tooltips=[("Exp.", "$y{0}")],
            )

            intensity_min = np.min(intensity_matrix)
            intensity_max = np.max(intensity_matrix)
            color_mapper = LinearColorMapper(
                palette="Viridis256", low=intensity_min, high=intensity_max
            )

            heatmap_figure.image(
                image=[intensity_matrix],
                x=max(ppm_values),
                y=time_range["start"],
                dw=abs(max(ppm_values) - min(ppm_values)),
                dh=time_range["end"] - time_range["start"],
                color_mapper=color_mapper,
                level="image",
            )

            heatmap_figure.grid.grid_line_width = 0
            color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12)
            heatmap_figure.add_layout(color_bar, "right")

            nmrplot_figure = figure(
                y_axis_label="intensity",
                aspect_ratio=2,
                x_range=shared_x_range,
                y_range=(intensity_min, intensity_max),
            )
            nmrplot_figure.line(x="δ (ppm)", y="intensity", source=line_source)

            echemplot_figure = figure(
                x_axis_label="voltage (V)",
                y_axis_label="t (h)",
                y_range=shared_y_range,
                height=400,
                width=250,
            )
            if echem_data and "Voltage" in echem_data and "time" in echem_data:
                echem_source = ColumnDataSource(
                    data={"time": echem_data["time"], "voltage": echem_data["Voltage"]}
                )

                echemplot_figure.line(
                    x="voltage",
                    y="time",
                    source=echem_source,
                )

            line_y_range = nmrplot_figure.y_range
            line_y_range.js_link("start", color_mapper, "low")
            line_y_range.js_link("end", color_mapper, "high")

            crosshair = CrosshairTool(dimensions="width", line_color="grey")
            heatmap_figure.add_tools(crosshair)
            echemplot_figure.add_tools(crosshair)

            heatmap_figure.js_on_event(
                DoubleTap, CustomJS(args=dict(p=heatmap_figure), code="p.reset.emit()")
            )
            nmrplot_figure.js_on_event(
                DoubleTap, CustomJS(args=dict(p=nmrplot_figure), code="p.reset.emit()")
            )
            echemplot_figure.js_on_event(
                DoubleTap, CustomJS(args=dict(p=echemplot_figure), code="p.reset.emit()")
            )

            hover = heatmap_figure.select_one(HoverTool)

            hover.callback = CustomJS(
                args=dict(
                    line_source=line_source,
                    spectra_intensities=spectra_intensities,
                    ppm_values=ppm_values.tolist(),
                ),
                code="""
                const geometry = cb_data['geometry'];
                const index = Math.max(0, Math.min(Math.floor(geometry.y), spectra_intensities.length - 1));

                var data = line_source.data;
                data['intensity'] = spectra_intensities[index];
                line_source.change.emit();
                """,
            )

            hover.mode = "hline"
            echemplot_figure.add_tools(hover)

            heatmap_figure.x_range.js_on_change(
                "start",
                CustomJS(
                    args=dict(
                        color_mapper=color_mapper,
                        intensity_matrix=intensity_matrix.tolist(),
                        ppm_array=ppm_values.tolist(),
                    ),
                    code="""
                    const start_index = ppm_array.findIndex(ppm => ppm <= cb_obj.end);
                    const end_index = ppm_array.findIndex(ppm => ppm <= cb_obj.start);

                    let min_intensity = Infinity;
                    let max_intensity = -Infinity;

                    for (let i = 0; i < intensity_matrix.length; i++) {
                        for (let j = start_index; j <= end_index; j++) {
                            if (j >= 0 && j < intensity_matrix[i].length) {
                                const value = intensity_matrix[i][j];
                                min_intensity = Math.min(min_intensity, value);
                                max_intensity = Math.max(max_intensity, value);
                            }
                        }
                    }

                    color_mapper.low = min_intensity;
                    color_mapper.high = max_intensity;
                    """,
                ),
            )

            heatmap_figure.x_range.tags = [ppm_values.tolist(), intensity_matrix.tolist()]

            grid = [[None, nmrplot_figure], [echemplot_figure, heatmap_figure]]
            gp = gridplot(grid, merge_tools=True)

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(gp, theme=DATALAB_BOKEH_THEME)

            return self.data.get("time_data"), ["Plot successfully generated"]

        except Exception as e:
            import traceback

            LOGGER.error(f"Error in generate_insitu_nmr_plot: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return None, []
