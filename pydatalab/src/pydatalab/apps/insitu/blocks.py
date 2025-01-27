from pathlib import Path
from typing import List, Tuple, Union

import bokeh.embed
import pandas as pd
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
            nmr_data, df = process_data(
                item_id="bc_insitu_block",
                folder_name="Example-TEGDME.zip",
                nmr_folder_name="2023-08-11_jana_insituLiLiTEGDME-02_galv",
                echem_folder_name="LiLiTEGDMEinsitu_02",
                ppm1=ppm1,
                ppm2=ppm2,
            )
            self.data["nmr_data"] = {
                "processed_data": df.to_dict(),
                "parameters": nmr_data.get("parameters", {}),
            }

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

            return df, ["Plot successfully generated"]

        except Exception as e:
            LOGGER.error(f"Error in generate_insitu_nmr_plot: {str(e)}")
            return None, []
