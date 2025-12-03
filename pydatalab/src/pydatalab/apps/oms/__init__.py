import os
from pathlib import Path

import bokeh.embed
import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import Button, CustomJS, HoverTool, Legend
from bokeh.palettes import Category10_10
from bokeh.plotting import ColumnDataSource, figure

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, TOOLS
from pydatalab.file_utils import get_file_info_by_id


class OMSBlock(DataBlock):
    blocktype = "oms"
    name = "OMS"
    description = "Block for plotting OMS time series data."
    accepted_file_extensions: tuple[str, ...] = (".csv",)

    @property
    def plot_functions(self):
        return (self.generate_oms_plot,)

    @classmethod
    def parse_oms_csv(cls, filename: Path) -> pd.DataFrame:
        """Parses .csv OMS data from mass spectrometer

        The file consists of a header with metadata. The header size is specified
        in a line containing "header" (e.g., "header",0000000026,"lines"), normally on line 2.
        This method searches the first 10 lines for this information.

        Args:
            filename: Path to the .csv file

        Returns:
            OMS dataframe with time and species concentration columns.
        """
        # Search the first 10 lines for the header size
        header_size = None
        with open(filename) as f:
            for i in range(10):
                line = f.readline()
                if not line:
                    break
                if "header" in line.lower():
                    # Parse the header size from the line
                    # Format: "header",0000000026,"lines"
                    header_parts = line.strip().split(",")
                    header_size = int(header_parts[1])
                    break

        if header_size is None:
            raise ValueError("Could not find header size information in the first 10 lines")

        # Read the data, skipping the header, added +1 as the header seemed to appear one line lower...
        oms_data = pd.read_csv(filename, skiprows=header_size + 1)

        # Drop any unnamed columns (caused by trailing commas in the CSV)
        oms_data = oms_data.loc[:, ~oms_data.columns.str.contains("^Unnamed")]

        # Convert milliseconds to seconds
        if "ms" in oms_data.columns:
            oms_data["Time (s)"] = oms_data["ms"] / 1000.0

        return oms_data

    @staticmethod
    def _format_oms_plot(oms_data: pd.DataFrame) -> bokeh.layouts.layout:
        """Formats OMS data for plotting in Bokeh with all species plotted and toggleable legends

        Args:
            oms_data: OMS dataframe with time and species columns

        Returns:
            bokeh.layouts.layout: Bokeh layout with OMS data plotted
        """
        # Get all columns except Time, ms, and Time (s)
        species_columns = [col for col in oms_data.columns if col not in ["Time", "ms", "Time (s)"]]

        # Calculate mean of all species for the dummy hover glyph
        oms_data["_mean_concentration"] = oms_data[species_columns].mean(axis=1)

        # Create a ColumnDataSource (shared between both plots)
        source = ColumnDataSource(oms_data)

        # Plot all species with different colors
        colors = Category10_10

        # Helper function to create a plot with given y_axis_type
        def create_plot(y_axis_type):
            p = figure(
                sizing_mode="scale_width",
                aspect_ratio=1.5,
                x_axis_label="Time (s)",
                y_axis_label="Concentration",
                tools=TOOLS,
                y_axis_type=y_axis_type,
            )

            p.toolbar.logo = "grey"
            p.xaxis.ticker.desired_num_ticks = 5
            p.yaxis.ticker.desired_num_ticks = 5

            # Create an invisible dummy glyph for hover that won't be hidden by legend
            # Use mean concentration to stay within the data range
            dummy_hover_glyph = p.line(
                x="Time (s)",
                y="_mean_concentration",  # Use mean to stay in concentration range
                source=source,
                alpha=0,  # Completely invisible
                level="overlay",  # Ensure it's on top for hover
            )

            legend_items = []

            for i, species in enumerate(species_columns):
                color = colors[i % len(colors)]

                # Plot line
                line = p.line(
                    x="Time (s)", y=species, source=source, color=color, line_width=2, name=species
                )

                # Plot points
                circle = p.circle(
                    x="Time (s)", y=species, source=source, color=color, size=4, name=species
                )

                # Add to legend items
                legend_items.append((species, [line, circle]))

            # Create external legend with click policy
            legend = Legend(
                items=legend_items,
                click_policy="hide",
                background_fill_alpha=0.8,
                label_text_font_size="9pt",
                spacing=1,
                margin=5,
            )
            p.add_layout(legend, "right")

            # Build tooltips dynamically for each species with scientific notation
            tooltips = [("Time", "@{Time (s)}{0,0.0} s")]
            formatters = {}

            for species in species_columns:
                tooltips.append((species, f"@{{{species}}}{{%0.2e}}"))
                formatters[f"@{{{species}}}"] = "printf"

            # Add hover tool attached to only the dummy glyph
            hover = HoverTool(
                tooltips=tooltips,
                formatters=formatters,
                renderers=[dummy_hover_glyph],
                mode="vline",
                line_policy="none",
            )
            p.add_tools(hover)

            return p

        # Create both linear and log plots
        p_linear = create_plot("linear")
        p_log = create_plot("log")

        # Set initial visibility
        p_linear.visible = True
        p_log.visible = False

        # Add log/linear scale toggle button
        scale_button = Button(
            label="Log scale", button_type="default", width_policy="min", margin=(2, 5, 2, 5)
        )

        # Callback to switch which plot is visible (bokeh can't dynamically change scale as far as I'm aware)
        scale_callback = CustomJS(
            args=dict(btn=scale_button, p_linear=p_linear, p_log=p_log),
            code="""
                if (btn.label === 'Log scale') {
                    p_linear.visible = false;
                    p_log.visible = true;
                    btn.label = 'Linear scale';
                    btn.button_type = 'default';
                } else {
                    p_linear.visible = true;
                    p_log.visible = false;
                    btn.label = 'Log scale';
                    btn.button_type = 'default';
                }
            """,
        )

        scale_button.js_on_click(scale_callback)

        # Create controls layout
        controls_layout = row(scale_button, sizing_mode="scale_width", margin=(10, 0, 10, 0))

        layout = column(controls_layout, p_linear, p_log, sizing_mode="scale_width")

        return layout

    def generate_oms_plot(self):
        file_info = None
        oms_data = None

        if "file_id" not in self.data:
            return

        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()

        if ext not in self.accepted_file_extensions:
            raise ValueError(
                f"Extension not in recognised extensions: {self.accepted_file_extensions}"
            )
        elif ext == ".csv":
            oms_data = self.parse_oms_csv(Path(file_info["location"]))

        if oms_data is not None:
            layout = self._format_oms_plot(oms_data)
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(layout, theme=DATALAB_BOKEH_THEME)
