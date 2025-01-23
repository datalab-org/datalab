from pathlib import Path
from typing import List, Tuple

import bokeh.embed
import pandas as pd
from datalab_app_plugin_nmr_insitu import process_data

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

    @property
    def plot_functions(self):
        return (self.generate_insitu_nmr_plot,)

    def generate_insitu_nmr_plot(
        self, ppm1: float | None = None, ppm2: float | None = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        file_info = None
        nmr_data = None
        df = None

        if "file_id" not in self.data:
            LOGGER.warning("No file set in the DataBlock")
            return None, []

        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = Path(file_info["location"]).suffix.lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "Unsupported file extension (must be one of %s, not %s)",
                    self.accepted_file_extensions,
                    ext,
                )
                return None, []

            ppm1 = float(self.data.get("ppm1", self.defaults["ppm1"]))
            ppm2 = float(self.data.get("ppm2", self.defaults["ppm2"]))

            try:
                # file_name = Path(file_info["location"]).name

                nmr_data, df = process_data(
                    # item_id=file_info["item_ids"][0],
                    # file_name=file_name,
                    item_id="bc_nmr_insitu",
                    file_name="demo_dataset_nmr_insitu.zip",
                    ppm1=ppm1,
                    ppm2=ppm2,
                )
            except Exception as e:
                LOGGER.error(f"Error processing insitu NMR data: {str(e)}")
                return None, []

        if df is not None:
            try:
                plot = selectable_axes_plot(
                    df,
                    x_options=["time"],
                    y_options=["intensity", "norm_intensity"],
                    plot_points=True,
                    plot_line=True,
                )
                self.data["bokeh_plot_data"] = bokeh.embed.json_item(
                    plot, theme=DATALAB_BOKEH_THEME
                )
                return df, ["Plot successfully generated"]
            except Exception as e:
                LOGGER.error(f"Error generating plot: {str(e)}")
                return None, []
        else:
            return None, []
