from pathlib import Path
from typing import List, Tuple, Union

import bokeh.embed
import numpy as np
import pandas as pd
from bokeh.layouts import row
from bokeh.models import ColorBar, LinearColorMapper, Range1d
from bokeh.plotting import figure
from datalab_app_plugin_nmr_insitu import fitting_data, process_data

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER


class InsituBlock(DataBlock):
    blocktype = "insitu"
    name = "NMR insitu"
    description = "A simple NMR insitu block from .zip files."
    accepted_file_extensions = (".zip",)

    defaults = {"ppm1": 220, "ppm2": 310}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.data, "get"):
            self.data = {}
        self.data.setdefault("ppm1", self.defaults["ppm1"])
        self.data.setdefault("ppm2", self.defaults["ppm2"])

    @property
    def plot_functions(self):
        return (self.generate_insitu_nmr_plot,)

    def process_and_store_data(self) -> bool:
        try:
            ppm1 = float(self.data.get("ppm1", self.defaults["ppm1"]))
            ppm2 = float(self.data.get("ppm2", self.defaults["ppm2"]))

            # Process data
            nmr_data, df, echem_df = process_data(
                item_id="bc_insitu_block",
                folder_name="Example-TEGDME.zip",
                nmr_folder_name="2023-08-11_jana_insituLiLiTEGDME-02_galv",
                echem_folder_name="LiLiTEGDMEinsitu_02",
                ppm1=ppm1,
                ppm2=ppm2,
            )

            self.data["nmr_data"] = {
                "processed_data": df.to_dict(),
                "nmr_data": nmr_data.to_dict(),
            }

            echem_df_clean = echem_df.copy()
            echem_df_clean = echem_df_clean.replace([np.inf, -np.inf], np.nan)
            echem_df_clean = echem_df_clean.fillna("null")

            for column in echem_df_clean.columns:
                if echem_df_clean[column].dtype == "float64":
                    echem_df_clean[column] = echem_df_clean[column].replace("null", None)
                    echem_df_clean[column] = echem_df_clean[column].astype("float")
                elif echem_df_clean[column].dtype == "int64":
                    echem_df_clean[column] = echem_df_clean[column].replace("null", None)
                    echem_df_clean[column] = echem_df_clean[column].astype("int")

            self.data["echem_df"] = {"processed_data": echem_df_clean.to_dict()}

            fitting_results = fitting_data(nmr_data, df)

            self.data["fitting_results"] = {
                "data_df": pd.DataFrame(fitting_results["data_df"]).to_dict(),
                "df_peakfit1": pd.DataFrame(fitting_results["df_peakfit1"]).to_dict(),
                "df_peakfit2": pd.DataFrame(fitting_results["df_peakfit2"]).to_dict(),
            }

            self.data["processing_params"] = {
                "ppm1": ppm1,
                "ppm2": ppm2,
                "file_id": self.data.get("file_id"),
            }

            return True

        except Exception as e:
            LOGGER.error(f"Error processing data: {str(e)}")
            return False

    def should_reprocess_data(self) -> bool:
        if "processing_params" not in self.data:
            return True

        params = self.data["processing_params"]
        current_ppm1 = float(self.data.get("ppm1", self.defaults["ppm1"]))
        current_ppm2 = float(self.data.get("ppm2", self.defaults["ppm2"]))
        current_file_id = self.data.get("file_id")

        return (
            params.get("ppm1") != current_ppm1
            or params.get("ppm2") != current_ppm2
            or params.get("file_id") != current_file_id
            or "nmr_data" not in self.data
            or "fitting_results" not in self.data
        )

    def generate_insitu_nmr_plot(
        self, ppm1: Union[float, None] = None, ppm2: Union[float, None] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return None, []

        try:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = Path(file_info["location"]).suffix.lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )
                return None, []

            if self.should_reprocess_data():
                LOGGER.info("Processing new data...")
                if not self.process_and_store_data():
                    return None, []
            else:
                LOGGER.info("Using stored data...")

            df = pd.DataFrame(self.data["nmr_data"]["processed_data"])
            fitting_results = self.data["fitting_results"]

            plot = selectable_axes_plot(
                df,
                x_options=["time"],
                y_options=["intensity", "norm_intensity"],
                plot_points=True,
                plot_line=True,
                plot_height=700,
                plot_width=400,
            )
            self.data["bokeh_plot_data_1"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)

            plot_combined = figure(
                x_axis_label="Time",
                y_axis_label="Intensity",
                plot_height=700,
                plot_width=400,
            )

            data_df = pd.DataFrame(fitting_results["data_df"])
            df_peakfit1 = pd.DataFrame(fitting_results["df_peakfit1"])
            df_peakfit2 = pd.DataFrame(fitting_results["df_peakfit2"])

            plot_combined.line(
                data_df["time"],
                data_df["intensity"],
                line_color="blue",
                legend_label="Original",
            )
            plot_combined.circle(data_df["time"], data_df["intensity"], color="blue", size=5)

            plot_combined.line(
                df_peakfit1["time"],
                df_peakfit1["intensity"],
                line_color="red",
                legend_label="Peak 1",
            )
            plot_combined.circle(df_peakfit1["time"], df_peakfit1["intensity"], color="red", size=5)

            plot_combined.line(
                df_peakfit2["time"],
                df_peakfit2["intensity"],
                line_color="green",
                legend_label="Peak 2",
            )
            plot_combined.circle(
                df_peakfit2["time"], df_peakfit2["intensity"], color="green", size=5
            )

            plot_combined.legend.click_policy = "hide"

            self.data["bokeh_plot_data_2"] = bokeh.embed.json_item(
                plot_combined, theme=DATALAB_BOKEH_THEME
            )

            #! Temp echem
            echem_df = pd.DataFrame(self.data["echem_df"]["processed_data"])

            plot = selectable_axes_plot(
                echem_df,
                x_options=["time/s"],
                y_options=["Voltage"],
                plot_points=True,
                plot_line=True,
                plot_height=700,
                plot_width=400,
            )
            self.data["bokeh_plot_data_3"] = bokeh.embed.json_item(plot, theme=DATALAB_BOKEH_THEME)

            #!

            echem_plot = figure(
                x_axis_label="Voltage",
                y_axis_label="Time (s)",
                plot_height=700,
                plot_width=400,
            )

            nmr_plot = figure(
                x_axis_label="ppm",
                y_axis_label="Intensity",
                plot_height=700,
                plot_width=400,
                # x_range=(max(ppm_values), min(ppm_values))
                y_axis_location="right",
            )

            echem_plot.line(
                echem_df["Voltage"],
                echem_df["time/s"],
                line_color="blue",
            )

            nmr_data = self.data["nmr_data"]["nmr_data"]
            if "index" in nmr_data:
                nmr_df = pd.DataFrame(
                    data=nmr_data["data"], columns=nmr_data["columns"], index=nmr_data["index"]
                )
            else:
                nmr_df = pd.DataFrame(nmr_data)

            ppm_values = nmr_df["ppm"].values

            num_experiments = len(nmr_df.columns) - 1
            colors = [
                f"#{int(255 * i/num_experiments):02x}00{int(255 * (1-i/num_experiments)):02x}"
                for i in range(num_experiments)
            ]
            for i in range(1, num_experiments + 1):
                col_name = str(i)
                if col_name in nmr_df.columns:
                    nmr_plot.line(
                        ppm_values,
                        nmr_df[col_name],
                        line_color=colors[i - 1],
                        line_alpha=0.5,
                    )

            nmr_plot.x_range.flipped = True

            # nmr_plot.legend.click_policy = "hide"
            # echem_plot.legend.click_policy = "hide"

            combined_plot = row(echem_plot, nmr_plot)

            self.data["bokeh_plot_data_4"] = bokeh.embed.json_item(
                combined_plot, theme=DATALAB_BOKEH_THEME
            )

            #! Heatmap

            ppm_values = nmr_df["ppm"].values
            time_values = self.data["nmr_data"]["processed_data"]["time"]

            intensity_matrix = np.array(
                [nmr_df[str(i)].values for i in range(1, len(nmr_df.columns))]
            )

            x_min, x_max = ppm_values.min(), ppm_values.max()
            y_min, y_max = time_values[0], time_values[599]

            color_mapper = LinearColorMapper(
                palette="Turbo256", low=intensity_matrix.min(), high=intensity_matrix.max()
            )

            heatmap_plot = figure(
                x_axis_label="ppm",
                y_axis_label="time (h)",
                plot_height=700,
                plot_width=400,
                y_axis_location="right",
            )

            heatmap_plot.image(
                image=[intensity_matrix],
                x=x_max,
                y=y_min,
                dw=x_max - x_min,
                dh=y_max - y_min,
                color_mapper=color_mapper,
            )

            color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))

            heatmap_plot.add_layout(color_bar, "right")

            self.data["bokeh_plot_data_5"] = bokeh.embed.json_item(
                heatmap_plot, theme=DATALAB_BOKEH_THEME
            )

            #!

            ppm_values = nmr_df["ppm"].values
            time_values = self.data["nmr_data"]["processed_data"]["time"]

            intensity_matrix = np.array(
                [nmr_df[str(i)].values for i in range(1, len(nmr_df.columns))]
            )

            echem_plot_2 = figure(
                x_axis_label="Voltage",
                y_axis_label="Time (h)",
                plot_height=700,
                plot_width=400,
                y_range=Range1d(start=y_min, end=y_max),
                min_border_right=0,
            )

            echem_plot_2.line(
                echem_df["Voltage"],
                echem_df["time/s"] / 3600,
                line_color="blue",
            )

            x_min, x_max = ppm_values.min(), ppm_values.max()
            y_min, y_max = time_values[0], time_values[599]

            color_mapper = LinearColorMapper(
                palette="Turbo256", low=intensity_matrix.min(), high=intensity_matrix.max()
            )

            heatmap_plot_2 = figure(
                x_axis_label="ppm",
                plot_height=700,
                plot_width=400,
                y_axis_location="right",
                x_range=Range1d(start=x_max, end=x_min),
                y_range=Range1d(start=y_min, end=y_max),
                min_border_left=0,
            )

            heatmap_plot_2.image(
                image=[intensity_matrix],
                x=x_max,
                y=y_min,
                dw=x_max - x_min,
                dh=y_max - y_min,
                color_mapper=color_mapper,
            )

            color_bar = ColorBar(color_mapper=color_mapper, location=(0, 0))

            heatmap_plot_2.add_layout(color_bar, "right")

            combined_plot_2 = row(echem_plot_2, heatmap_plot_2)

            self.data["bokeh_plot_data_6"] = bokeh.embed.json_item(
                combined_plot_2, theme=DATALAB_BOKEH_THEME
            )

            return df, ["Plot successfully generated"]

        except Exception as e:
            LOGGER.error(f"Error in generate_insitu_nmr_plot: {str(e)}")
            return None, []
