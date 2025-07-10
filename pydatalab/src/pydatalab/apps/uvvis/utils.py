from pathlib import Path

import numpy as np
import pandas as pd


def parse_uvvis_txt(filename: Path) -> pd.DataFrame:
    """
    Parses a UV-Vis .txt file into a pandas DataFrame
    Args:
        filename (Path): Path to the .txt file
    Returns:
        pd.DataFrame: DataFrame containing the UV-Vis data with columns for wavelength and absorbance
    """
    # Read the file, skipping the first 7 rows and using the first row as header
    data = pd.read_csv(filename, sep=r";", skiprows=7, header=None)

    # I need to look into what dark counts and reference counts are - I never used them just the sample counts from two differernt runs
    data.columns = ["Wavelength", "Sample counts", "Dark counts", "Reference counts"]
    return data


def find_absorbance(data_df, reference_df):
    """
    Calculates the absorbance from the sample and reference dataframes
    Args:
        data_df (pd.DataFrame): DataFrame containing the sample data
        reference_df (pd.DataFrame): DataFrame containing the reference data
    Returns:
        pd.DataFrame: DataFrame containing the absorbance data
    """
    # Calculate absorbance using Beer-Lambert Law
    absorbance = -np.log10(data_df["Sample counts"] / reference_df["Sample counts"])
    # Create a new DataFrame with the wavelength and absorbance
    absorbance_data = pd.DataFrame({"Wavelength": data_df["Wavelength"], "Absorbance": absorbance})
    return absorbance_data
