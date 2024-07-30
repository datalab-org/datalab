import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

def state_segmentation(df_full, stage_name):
    """Segment non-consecutive trials with a specific state into a list

    Parameters
    ----------
    df : pandas.core.frame.DataFrame
        Dataframe containing test rig data
    stage_name : str
        The specific stage you would like to separate from the full test rig data set

    Returns
    -------
    list_of_trials : list
        A list of all non-consecutive trial dataframes of the specific state_name
    """

    # Filter dataframe where state condition is satisfied
    filt = df_full["stage"] == stage_name
    df = df_full[filt].copy()

    # Create list of dataframes
    list_of_trials = [d for _, d in df.groupby(df.index - np.arange(len(df)))]

    return list_of_trials


class AdsorbAnalyze:
    def __init__(self, df):
        # Define attributes
        self.df = df

        # Extract adsorption trials
        self.adsorb_prep()

    @staticmethod
    def adsorb_filter(df0):
        """Filter the start and end times for the adsorption cycle

        Parameters
        ----------
        df0 : pandas.core.frame.DataFrame
            Original DataFrame containing all time records during adsorption

        Returns
        -------
        start_index : int
            The start index for an adsorption trial
        end_index : int
            The end index for an adsorption trial
        """

        # Create a copy of the dataframe
        df = df0.copy()

        # Select starting index -- unchanged for now
        start_index = df.index[0]

        # Define tolerances and constant variables for identifying steady signal readings
        abs_error = 0.02  # % difference in reading and steady-state value
        st_dev = 3e-3  # Standard deviation tolerance level
        window_size = 20  # Window size for rolling calculation
        column_name = "co2_out_unitless"

        # Select end index
        y = df[column_name]
        y_std = y.rolling(window_size).std()
        filt = y_std < st_dev

        if filt.any():
            # Calculate index at stop condition
            end_index = y.index[filt][0]

            # Verify final reading exceeds abs_error of expected steady-state reading
            y_err_bool = (1 - y.loc[end_index]) > abs_error

            if y_err_bool:
                # Do not apply filter and select final adsorption time reading
                end_index = y.index[-1]

        else:
            # Do not apply filter and select final adsorption time reading
            end_index = y.index[-1]

        return start_index, end_index

    def adsorb_prep(self):
        """Create adsorption dataframe containing all relevant information to calculate adsorption metrics

        Parameters
        ----------
        df0 : pandas.core.frame.DataFrame
            Original DataFrame with standardized column names but nonstandard stage definition
        """

        # Create copy of dataframe
        df = self.df

        # Segment adsorption and desorption trials
        df_preadsorb = state_segmentation(df, "pre_adsorb")
        df_adsorb = state_segmentation(df, "adsorb")

        # Add necessary columns
        for i, (pre, ads) in enumerate(zip(df_preadsorb, df_adsorb)):
            # Add CO2 inlet concentration
            co2_in_ppm = pre[-10:]["co2_out_ppm"].median()
            ads["co2_in_ppm"] = co2_in_ppm

            # Add H2O inlet concentration
            h2o_in_rh = pre[-10:]["relative_humidity_out_percent"].median()
            ads["relative_humidity_in_percent"] = h2o_in_rh

            # Add scaled co2 out
            ads["co2_out_unitless"] = ads["co2_out_ppm"] / co2_in_ppm

            # Add molar flow rate column
            y_co2 = ads["co2_in_ppm"] / 1e6  # co2 mole fraction
            co2_molar_flow = (ads["total_vol_flow_rate_ml_per_min"] * 1000) / (
                1000 * 22.4 * 60
            )  # mmol_co2 / s
            ads["co2_molar_flow_mmol_per_s"] = co2_molar_flow * y_co2

            # Add time columns
            time_s = ads["elapsed_time_s"] - ads["elapsed_time_s"].iloc[0]
            ads["time_s"] = time_s
            ads["time_min"] = time_s / 60

            # Apply adsorption time filtering algorithm
            start_index, end_index = AdsorbAnalyze.adsorb_filter(ads)

            # Replace adsorb list element with correct value
            df_adsorb[i] = ads.loc[start_index:end_index]

        # Store adsorption trials as attribute
        self.adsorb_trials = df_adsorb

    def co2_uptake(self, sorbent_mass_g, single_point=True):
        """Calculate the co2 uptake adsorption capacity in units of mmol_co2 adsorbed per gram of sorbent

        Parameters
        ----------
        sorbent_mass_g : float
            The sorbent mass in units of grams
        single_point : bool, optional
            Whether to calculate the final adsorption capacity at the end of the adsorption cycle (single_point=True)
            or calculate the co2 adsorption capacity as a function of time (single_point=False). The default is True.
            If single_point = True, the function will return a list of floats otherwise this function will return a list of pandas
            DataFrames.

        Returns
        -------
        return_array : list
            A list of co2 uptake capacities.
        """

        # Create empty list
        return_array = []

        # Iterate through all adsorption trials
        for ads in self.adsorb_trials:
            # Calculate difference in co2 concentration
            c_diff = (ads["co2_in_ppm"] - ads["co2_out_ppm"]) / ads[
                "co2_in_ppm"
            ]  # unitless

            # Calculate integrand
            integrand = ads["co2_molar_flow_mmol_per_s"] * c_diff  # mmol / s

            # Calculate uptake
            co2_capacity = cumulative_trapezoid(integrand, ads["time_s"], initial=0)

            # Normalized by sorbent mass
            co2_capacity /= sorbent_mass_g

            # Update format based on single_point boolean
            if single_point:
                co2_capacity = co2_capacity[-1]
            else:
                co2_capacity = pd.DataFrame(
                    {
                        "time_s": ads["time_s"],
                        "time_min": ads["time_min"],
                        "co2_uptake_mmolco2_per_gsorbent": co2_capacity,
                    }
                )

            # Store calculated value
            return_array.append(co2_capacity)

        return return_array

    def co2_breakthrough_plot(self, trial_num, time_unit="min"):
        """Plot the co2 breakthrough curve

        Parameters
        ----------
        trial_num : int
            The trial number. The first trial should start at 1.
        time_unit : str, optional
            The unit for the time x-axis. Valid options are "s" for seconds or "min" for minutes. The default value is "min".
        """
        # Decrement trial number
        trial_num -= 1

        # Extract specific adsorption trial
        adsorb_trial = self.adsorb_trials[trial_num]

        # Identify unit
        if time_unit == "s":
            time_column = "time_s"
            x_label = "Time (s)"
        else:
            time_column = "time_min"
            x_label = "Time (min)"

        # Create plot
        fig, ax = plt.subplots()
        ax.plot(adsorb_trial[time_column], adsorb_trial["co2_in_ppm"], "r")
        ax.plot(adsorb_trial[time_column], adsorb_trial["co2_out_ppm"], "b")
        ax.set_title("CO$_2$ Breakthrough Curve")
        ax.set_xlabel(x_label)
        ax.set_ylabel("CO$_2$ Concentration (ppm)")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend(("CO$_2$ In", "CO$_2$ Out"), loc="lower right")

        return fig

    def h2o_breakthrough_plot(self, trial_num, time_unit="min"):
        """Plot the h2o breakthrough curve

        Parameters
        ----------
        trial_num : int
            The trial number. The first trial should start at 1
        time_unit : str, optional
            The unit for the time x-axis. Valid optios are "s" for seconds or "min" for minutes. The default value is "min".
        """

        # Decrement trial number
        trial_num -= 1

        # Extract specific adsorption trial
        adsorb_trial = self.adsorb_trials[trial_num]

        # Identify unit
        if time_unit == "s":
            time_column = "time_s"
            x_label = "Time (s)"
        else:
            time_column = "time_min"
            x_label = "Time (min)"

        # Create plot
        fig, ax = plt.subplots()
        ax.plot(
            adsorb_trial[time_column], adsorb_trial["relative_humidity_in_percent"], "r"
        )
        ax.plot(
            adsorb_trial[time_column],
            adsorb_trial["relative_humidity_out_percent"],
            "b",
        )
        ax.set_title("H$_2$O Breakthrough Curve")
        ax.set_xlabel(x_label)
        ax.set_ylabel("Relative Humidity (%)")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend(("H$_2$O In", "H$_2$O In"), loc="lower right")

        return fig

    def co2_uptake_plot(self, sorbent_mass_g, trial_num, time_unit="min"):
        """Plot the co2 uptake curve

        Parameters
        ----------
        sorbent_mass_g : float
            The sorbent mass in units of grams
        trial_num : int
            The trial number. The first trial should start at 1
        time_unit : str, optional
            The unit for the time x-axis. Valid options are "s" for seconds or "min" for minutes. The default value is "min".

        Returns
        -------
        fig : matplotlib.figure.Figure
            A matplotlib figure of the co2 uptake
        """

        # Decrement trial number
        trial_num -= 1

        # Calculate CO2 uptake
        ads_uptakes = self.co2_uptake(sorbent_mass_g, single_point=False)

        # Extract specific adsorption trial
        ads_uptake = ads_uptakes[trial_num]

        # Identify unit
        if time_unit == "s":
            time_column = "time_s"
            x_label = "Time (s)"
        else:
            time_column = "time_min"
            x_label = "Time (min)"

        # Create plot
        fig, ax = plt.subplots()
        ax.plot(
            ads_uptake[time_column], ads_uptake["co2_uptake_mmolco2_per_gsorbent"], "k"
        )
        ax.set_title("CO$_2$ Adsorption Uptake")
        ax.set_xlabel(x_label)
        ax.set_ylabel("CO$_2$ Amount Adsorbed (mmol$_{CO2}$ / g$_{sorbent}$)")
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        return fig

