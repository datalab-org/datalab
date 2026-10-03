import tempfile
import warnings
import zipfile
from pathlib import Path

import bokeh
import numpy as np
import pandas as pd
from bokeh.events import DoubleTap
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    HoverTool,
    Legend,
    LegendItem,
    Segment,
    Span,
)
from bokeh.plotting import figure

from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

TOOLS = "box_zoom, reset, crosshair, save"


def _parse_output_file(path: Path) -> pd.DataFrame | None:
    """Parse a TOPAS-style 3-column refinement output file (2θ, Yobs, Ycalc)."""
    try:
        df = pd.read_csv(path, sep=r"\s+", header=None, dtype=float)
        if df.shape[1] >= 3:
            df = df.iloc[:, :3]
            df.columns = ["two_theta", "yobs", "ycalc"]
            return df
    except Exception:
        LOGGER.debug("Could not parse %s as 3-column output file", path, exc_info=True)
    return None


def _parse_hkl_file(path: Path) -> pd.DataFrame | None:
    """Parse a 7-column HKL reflection file (h k l M d 2θ I)."""
    try:
        df = pd.read_csv(path, sep=r"\s+", header=None, comment="#", dtype=float)
        if df.shape[1] >= 7:
            df = df.iloc[:, :7]
            df.columns = ["h", "k", "l", "M", "d", "two_theta", "intensity"]
            return df
    except Exception:
        LOGGER.debug("Could not parse %s as HKL reflection file", path, exc_info=True)
    return None


def _detect_files(
    extract_dir: Path,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Find and parse the output and HKL files inside an extracted zip directory."""
    output_df = None
    hkl_df = None

    all_files = sorted(extract_dir.rglob("*"))
    text_files = [f for f in all_files if f.is_file() and not f.name.startswith(".")]

    # Prefer files named output.txt / hkl.txt, then fall back to column-count sniffing
    named_output = next((f for f in text_files if f.name.lower() == "output.txt"), None)
    named_hkl = next((f for f in text_files if f.name.lower() == "hkl.txt"), None)

    if named_output:
        output_df = _parse_output_file(named_output)
    if named_hkl:
        hkl_df = _parse_hkl_file(named_hkl)

    # Fall back: try every remaining file and guess by column count
    for f in text_files:
        if output_df is not None and hkl_df is not None:
            break
        try:
            df = pd.read_csv(f, sep=r"\s+", header=None, comment="#", dtype=float, nrows=5)
        except Exception:
            LOGGER.debug("Skipping file during format sniffing: %s", f, exc_info=True)
            continue

        ncols = df.shape[1]
        if output_df is None and ncols == 3 and f != named_output:
            candidate = _parse_output_file(f)
            if candidate is not None:
                output_df = candidate
        elif hkl_df is None and ncols >= 7 and f != named_hkl:
            candidate = _parse_hkl_file(f)
            if candidate is not None:
                hkl_df = candidate

    return output_df, hkl_df


def _build_refinement_plot(output_df: pd.DataFrame, hkl_df: pd.DataFrame | None):
    """Build a Bokeh figure showing observed, calculated, residual, and (optionally) HKL ticks."""

    two_theta = output_df["two_theta"].to_numpy()
    yobs = output_df["yobs"].to_numpy()
    ycalc = output_df["ycalc"].to_numpy()
    residual_raw = yobs - ycalc

    ymax = max(yobs.max(), ycalc.max())
    ymin = yobs.min()
    yrange = ymax - ymin

    # Place residual below the pattern with a gap
    residual_offset = ymin - 0.20 * yrange
    residual = residual_raw + residual_offset

    p = figure(
        sizing_mode="scale_width",
        aspect_ratio=2.5,
        x_axis_label="2θ (°)",
        y_axis_label="Intensity",
        tools=TOOLS,
    )
    p.toolbar.logo = "grey"
    p.xaxis.ticker.desired_num_ticks = 10
    p.yaxis.ticker.desired_num_ticks = 5

    main_source = ColumnDataSource(
        {"two_theta": two_theta, "yobs": yobs, "ycalc": ycalc, "residual": residual}
    )

    r_obs = p.circle(
        x="two_theta",
        y="yobs",
        source=main_source,
        size=3,
        color="black",
        legend_label="Observed",
    )
    r_calc = p.line(
        x="two_theta",
        y="ycalc",
        source=main_source,
        color="red",
        line_width=1.5,
        legend_label="Calculated",
    )
    r_resid = p.line(
        x="two_theta",
        y="residual",
        source=main_source,
        color="green",
        line_width=1,
        legend_label="Residual",
    )

    zero_line = Span(
        location=residual_offset,
        dimension="width",
        line_color="gray",
        line_dash="dashed",
        line_width=1,
    )
    p.add_layout(zero_line)

    p.add_tools(
        HoverTool(
            renderers=[r_obs],
            tooltips=[("2θ", "@two_theta{0.000}°"), ("Obs", "@yobs{0.0}"), ("Calc", "@ycalc{0.0}")],
            mode="vline",
        )
    )

    legend_items = [
        LegendItem(label="Observed", renderers=[r_obs]),
        LegendItem(label="Calculated", renderers=[r_calc]),
        LegendItem(label="Residual", renderers=[r_resid]),
    ]

    # HKL tick marks
    if hkl_df is not None:
        hkl_sorted = hkl_df.sort_values("two_theta")
        norm_intensity = hkl_sorted["intensity"].to_numpy()
        max_i = norm_intensity.max()
        if max_i > 0:
            norm_intensity = norm_intensity / max_i

        tick_base = residual_offset - 0.08 * yrange
        tick_top = tick_base - norm_intensity * 0.10 * yrange

        hkl_source = ColumnDataSource(
            {
                "x0": hkl_sorted["two_theta"].to_numpy(),
                "x1": hkl_sorted["two_theta"].to_numpy(),
                "y0": np.full(len(hkl_sorted), tick_base),
                "y1": tick_top,
                "h": hkl_sorted["h"].astype(int).astype(str).to_numpy(),
                "k": hkl_sorted["k"].astype(int).astype(str).to_numpy(),
                "l": hkl_sorted["l"].astype(int).astype(str).to_numpy(),
            }
        )

        r_hkl = p.add_glyph(
            hkl_source, Segment(x0="x0", y0="y0", x1="x1", y1="y1", line_color="blue", line_width=1)
        )
        r_hkl.hover_glyph = None

        p.add_tools(
            HoverTool(
                renderers=[r_hkl],
                tooltips=[("hkl", "(@h @k @l)"), ("2θ", "@x0{0.000}°")],
            )
        )

        legend_items.append(LegendItem(label="Reflections", renderers=[r_hkl]))

    # Move legend outside the plot, with click_policy="hide" for toggling
    p.legend.visible = False
    external_legend = Legend(
        items=legend_items,
        click_policy="hide",
        background_fill_alpha=0.8,
        spacing=2,
        margin=2,
    )
    p.add_layout(external_legend, "right")

    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code="p.reset.emit()"))

    return p


class XRDRefinementBlock(DataBlock):
    blocktype = "xrd_refinement"
    name = "XRD Refinement"
    description = "Visualize Rietveld refinement results from a TOPAS output zip file."
    accepted_file_extensions = (".zip",)

    defaults: dict = {}

    @property
    def plot_functions(self):
        return (self.generate_refinement_plot,)

    def generate_refinement_plot(self) -> None:
        if not self.data.get("file_id"):
            return

        try:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        except Exception as exc:
            warnings.warn(f"XRDRefinementBlock: could not retrieve file: {exc}")
            return

        location = file_info.get("location")
        if not location or not zipfile.is_zipfile(location):
            warnings.warn(f"XRDRefinementBlock: file is not a valid zip archive: {location}")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            extract_dir = Path(tmpdir)
            try:
                with zipfile.ZipFile(location) as zf:
                    zf.extractall(extract_dir)
            except Exception as exc:
                warnings.warn(f"XRDRefinementBlock: failed to extract zip: {exc}")
                return

            output_df, hkl_df = _detect_files(extract_dir)

        if output_df is None:
            warnings.warn("XRDRefinementBlock: no 3-column output file found in zip")
            return

        if hkl_df is None:
            LOGGER.info("XRDRefinementBlock: no HKL file found; plotting without reflections")

        p = _build_refinement_plot(output_df, hkl_df)

        self.data["computed"] = {
            "n_points": len(output_df),
            "two_theta_range": [
                float(output_df["two_theta"].min()),
                float(output_df["two_theta"].max()),
            ],
            "n_reflections": len(hkl_df) if hkl_df is not None else 0,
        }
        self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=DATALAB_BOKEH_THEME)
