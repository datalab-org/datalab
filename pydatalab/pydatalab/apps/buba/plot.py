import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from bokeh.layouts import layout
from bokeh.models import (
    Range1d,
)
from bokeh.plotting import figure

from pydatalab.bokeh_plots import TOOLS


def buba_plot(
    analysed_data: dict,
    sorbent_mass_g: float | None = None,
    time_unit: str = "s",
    **kwargs,
) -> layout:
    """
    Creates Buba grid plot.

    Args:
        analysed_data: The results of the ad/desoprtion analysis.
        sorbent_mass_g: The sorbent mass used for normalization.
        time_unit: The desired unit for time axes ('s' or 'min').
        kwargs: Any additional options to pass to the bokeh Figure.

    Returns:
        Bokeh layout

    """

    common_options = {"tools": TOOLS}
    common_options.update(**kwargs)

    cmap = plt.get_cmap("inferno")
    color_space = np.linspace(0.3, 0.7, max(analysed_data["trial_index"]))

    # All CO2 uptakes
    x_label = "Trial number"
    if sorbent_mass_g is not None:
        y_label = "CO₂ adsorption capacity (mmol/g)"
    else:
        y_label = "Absolute CO₂ adsoprtion (mmol)"

    adsorption_capacity_per_trial_plot = figure(
        aspect_ratio=3, x_axis_label=x_label, y_axis_label=y_label, **common_options
    )

    ads_capacity_range = (0, 1.1 * np.max(analysed_data["ads_capacity_co2"]))

    for trial_ind in analysed_data["trial_index"]:
        trial_ind -= 1
        adsorption_capacity_per_trial_plot.circle(
            x=trial_ind,
            y=analysed_data["ads_capacity_co2"][trial_ind],
            fill_color="white",
            line_width=4,
            size=12,
            color=matplotlib.colors.rgb2hex(cmap(color_space[trial_ind])),
        )

    adsorption_capacity_per_trial_plot.y_range = Range1d(*ads_capacity_range)

    co2_breakthrough_plot = figure(
        x_axis_label=f"Time ({time_unit})", y_axis_label="CO₂ in:out", **common_options
    )

    co2_uptake_plot = figure(
        x_axis_label=f"Time ({time_unit})",
        y_axis_label="CO₂ Amount Adsorbed (mmol/g)",
        **common_options,
    )

    h2o_breakthrough_plot = figure(
        x_axis_label=f"Time ({time_unit})",
        y_axis_label="Relative humidity in:out",
        **common_options,
    )

    time_column = "time_s"

    for trial_ind in analysed_data["trial_index"]:
        trial_ind -= 1

        times = np.array(analysed_data[time_column][trial_ind])
        if time_unit == "min":
            times = times // 60

        co2_breakthrough_plot.line(
            x=times,
            y=np.array(analysed_data["co2_out_ppm"][trial_ind])
            / np.array(analysed_data["co2_in_ppm"][trial_ind]),
            line_width=2,
            color=matplotlib.colors.rgb2hex(cmap(color_space[trial_ind])),
        )
        co2_uptake_plot.line(
            x=times,
            y=analysed_data["co2_uptake_mmolco2_per_gsorbent"][trial_ind],
            line_width=2,
            color=matplotlib.colors.rgb2hex(cmap(color_space[trial_ind])),
        )
        h2o_breakthrough_plot.line(
            x=times,
            y=np.array(analysed_data["relative_humidity_in_percent"][trial_ind])
            / np.array(analysed_data["relative_humidity_out_percent"][trial_ind]),
            color=matplotlib.colors.rgb2hex(cmap(color_space[trial_ind])),
        )

    return layout(
        [
            [adsorption_capacity_per_trial_plot],
            [co2_uptake_plot, co2_breakthrough_plot, h2o_breakthrough_plot],
        ],
        sizing_mode="scale_both",
    )
