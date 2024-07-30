from pathlib import Path
from typing import Dict, Union

import pandas as pd
import numpy as np
import warnings
import dateutil

__all__ = ("parse_buba",)

class PreProcess:
    def __init__(self, dir_data, instrument_id):
        # Define attributes
        self.dir_data = dir_data
        self.instrument_id = instrument_id

        # Load tables as dataframes
        self.raw_load()
        self.data_clean()

    def raw_load(self):
        """Load raw data file"""
        # Load csv file
        self.df_raw = pd.read_csv(self.dir_data)

    @staticmethod
    def column_rename(df0, instrument_id):
        """Function that renames column headers

        Parameters
        ----------
        df0 : pandas.core.frame.DataFrame
            Original DataFrame with nonstandard column names
        instrument_id : int
            Instrument id

         Returns
        -------
        df : pandas.core.frame.DataFrame
            DataFrame with standardized column headers
        """

        # Create copy of dataframe
        df = df0.copy()

        if instrument_id == 1:
            # Define original column names
            columns_orig = [
                "Total Test Time Elapsed (Seconds)",
                "MFC1 - Reading",
                "MFC2 - Reading",
                "MFC3 - Reading",
                "MFC4 - Reading",
                "C02 Reading",
                "H20 Reading",
                "Stage",
                "Nitrogen Temp",
                "Reactor Temp",
            ]

            # Define new column names
            columns_new = [
                "elapsed_time_s",
                "stream1_vol_flow_rate_ml_per_min",
                "stream2_vol_flow_rate_ml_per_min",
                "stream3_vol_flow_rate_ml_per_min",
                "stream4_vol_flow_rate_ml_per_min",
                "co2_out_ppm",
                "h2o_out_mmolh2o_per_molgas",
                "stage",
                "bubbler_temperature_celsius",
                "reactor_temperature_celsius",
            ]

        # Rename columns
        df = pd.DataFrame(data=df[columns_orig].values, columns=columns_new)

        return df

    @staticmethod
    def column_add(df0, instrument_id):
        """Function that add relevant columns to dataframe

        Parameters
        ----------
        df0 : pandas.core.frame.DataFrame
            Original DataFrame with nonstandard column names
        instrument_id : int
            Instrument id

        Returns
        -------
        df : pandas.core.frame.DataFrame
            DataFrame with additional columns
        """

        # Define helper functions
        def antoine(temperature_celsius):
            """Antoine equation for calculating the saturation pressure of water

            Parameters
            ----------
            temperature : numpy.ndarray
                Water temperature in units of Celsius

            Returns
            -------
            p_sat : numpy.ndarray
                Water saturation vapor pressure in units of bar
            """

            # Define Antoine equation constants
            # Source: https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE&Plot=on
            A, B, C = (
                5.40221,
                1838.675,
                -31.737,
            )  # Valid for temperature range [273, 303] Kelvin
            temperature = temperature_celsius + 273.15  # Celsius --> Kelvin
            log10_p = A - (B / (temperature + C))
            p_sat = 10**log10_p

            # Handle and report warning if temperature outside valid range
            invalid_temp = np.logical_or(temperature < 273, temperature > 303)
            p_sat[invalid_temp] = np.nan

            if np.any(invalid_temp):
                warnings.warn(
                    "Antoine equation estimate might not be accurate, temperature outside of range"
                )

            return p_sat

        # Create copy of dataframe
        df = df0.copy()

        # Add columns
        if instrument_id == 1:
            # Calculate total volumetric flow rate
            ind_flows = ["stream" + str(i) + "_vol_flow_rate_ml_per_min" for i in range(1, 5)]

            # Calculate total volumetric flow rate
            df["total_vol_flow_rate_ml_per_min"] = df[ind_flows].sum(axis=1)

            # Calculate relative humidity
            y_h2o = (
                df["h2o_out_mmolh2o_per_molgas"] / 1000
            )  # mole fraction of water in air (unitless)
            p_sat = antoine(df["bubbler_temperature_celsius"])
            df["relative_humidity_out_percent"] = (
                100 * y_h2o * 1.01325 / antoine(df["bubbler_temperature_celsius"])
            )

        return df

    @staticmethod
    def stage_remap(df0, instrument_id):
        """Function to remap nonstandard stage names to standardized stage names and drop additional stages

        Parameters
        ----------
        df0 : pandas.core.frame.DataFrame
            Original DataFrame with standardized column names but nonstandard stage definition
        instrument_id : int
            Instrument id
        """

        # Create copy of dataframe
        df = df0.copy()

        if instrument_id == 1:
            # Create mapping dictionary
            map_dict = {
                "Pre-Run Feed": "pre_adsorb",
                "Adsorption": "adsorb",
                "Pre-Blend": "pre_adsorb",
                "Blend": "adsorb",
            }

        # Remap the stage column
        df["stage"] = df["stage"].map(map_dict)

        # Remove additional stages
        filt = df["stage"].isnull()
        df = df[~filt]

        return df

    @staticmethod
    def columns_to_numeric(df0, instrument_id):
        """Convert numeric column data types to type float

        Parameters
        ----------
        df0 : pandas.core.frame.DataFrame
            Original DataFrame with nonstandard column types
        instrument_id : int
            Instrument id
        """

        # Create copy of dataframe
        df = df0.copy()

        if instrument_id == 1:
            # Identify numeric columns
            df_columns = list(df.columns)
            df_columns.remove("stage")
            for column in df_columns:
                df[column] = pd.to_numeric(df[column])

        return df

    def data_clean(self):
        """Clean raw dataframe by applying cleaning helper functions

        Parameters
        ----------
        tr_key : str
            _description_
        """
        # Create a copy of df_raw
        df = self.df_raw.copy()

        # Apply column rename function
        df = PreProcess.column_rename(df, self.instrument_id)

        # Apply stage remap function
        df = PreProcess.stage_remap(df, self.instrument_id)

        # Apply add columns function
        df = PreProcess.column_add(df, self.instrument_id)

        # Enforce numeric columns are floats
        df = PreProcess.columns_to_numeric(df, self.instrument_id)

        # Store cleaned dataframe
        self.df = df


def parse_mt_mass_spec_ascii(path: Path) -> Dict[str, Union[pd.DataFrame, Dict]]:
    """Parses an .asc file containing MS results from a Mettler-Toledo
    spectrometer and returns a dictionary with keys `data` and `meta`,
    which themselves contain a dictionary of dataframes for each species
    with the species names/masses as keys, and a dictionary of
    metadata fields respectively.

    Parameters:
        path: The path of the file to parse.

    """

    header_keys = ("Sourcefile", "Exporttime", "Start Time", "End Time")
    data_keys = ("Time Relative [s]", "Partial Pressure [mbar]", "Ion Current [A]")
    header = {}
    species = []

    if not path.exists():
        raise RuntimeError(f"Provided path does not exist: {path!r}")

    with open(path) as f:
        # Read start of file until all header keys have been found
        max_header_lines = 8
        reads = 0
        header_end = None
        while reads < max_header_lines:
            line = f.readline().strip()
            reads += 1
            if line:
                for key in header_keys:
                    if key in line:
                        header[key] = line.split(key)[-1].strip()
            if all(k in header for k in header_keys):
                header_end = f.tell()
                break
        else:
            raise ValueError(
                f"Could not find all header keys in first {max_header_lines} lines of file."
            )

        for key in header_keys[1:]:
            if "time" in key.lower():
                header[key] = dateutil.parser.parse(header[key])  # type: ignore

        reads = 0
        max_species_lines = 10
        while reads < max_species_lines:
            line = f.readline().strip()
            reads += 1
            if not line:
                continue
            species = line.split()
            break
        else:
            raise ValueError(
                f"Could not find species list in lines {header_end}:{header_end + max_species_lines} lines of file."
            )

        # Read data with duplicated keys: will have (column number % number of data keys) appended to them
        # MT software also writes "---" if the value is missing, so parse these as NaNs to remove later
        df = pd.read_csv(f, sep="\t", header=0, parse_dates=False, na_values=["---"])
        ms_results: Dict[str, Union[pd.DataFrame, Dict]] = {}
        ms_results["meta"] = header
        ms_results["data"] = {}

        # Some files have Ion Current [A] or Partial Pressure [mbar] -- only rename those that are present
        present_keys = set(df.columns.values) & set(data_keys)
        for ind, specie in enumerate(species):
            # Loop over all species and rename the columns to remove the species name and disaggregate as a dict
            species_data_keys = [k + f"{'.' + str(ind) if ind != 0 else ''}" for k in present_keys]
            ms_results["data"][specie] = df[species_data_keys].rename(
                {mangled: original for mangled, original in zip(species_data_keys, present_keys)},
                axis="columns",
            )

            # Drop time axis as format cannot be easily inferred and data is essentially duplicated: "Start Time" in header
            # provides the timestamp of the first row
            ms_results["data"][specie].drop("Time", axis="columns", inplace=True, errors="ignore")

            # If the file was provided in an incomplete form, the final rows will be NaN, so drop them
            ms_results["data"][specie].dropna(inplace=True)

        return ms_results

def parse_buba(path: Path, instrument_id: int = 1) -> pd.DataFrame:
    return PreProcess(path, instrument_id).df
