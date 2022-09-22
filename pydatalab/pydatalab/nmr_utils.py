import itertools
import os
import re

import matplotlib.pyplot as plt
import nmrglue as ng
import numpy as np
import pandas as pd
from scipy import integrate

######################################################################################
# Functions for reading in NMR data files
######################################################################################


def read_bruker_1d(data, process_number=1, verbose=True, sample_mass_mg=None):
    """Read a 1D bruker nmr spectrum and return it as a df.

    arguments:

    data: The directory of the full bruker data file. You may also supply a df as this argument. In this case, the df is returned as is.
    process_number: The process number of the processed data you want to plot [default 1]
    verbose: Whether to print information such as the spectrum title to stdout (default True)
    sample_mass_mg: The (optional) sample mass. If provided, the resulting DataFrame will have a "intensity_per_scan_per_gram" column.
    """

    # if df is provided, just return it as-is. This functionality is provided to make functions calling read_bruker_1d flexible by default.
    # Either the data directory or the already-processed df can always be provided with equivalent results.

    if type(data) == pd.core.frame.DataFrame:
        if verbose:
            print("data frame provided to read_bruker_1d(). Returning it as is.")
        return data
    else:
        data_dir = data

    processed_data_dir = os.path.join(data_dir, "pdata", str(process_number))

    a_dic, a_data = ng.fileio.bruker.read(data_dir)  # aquisition_data
    p_dic, p_data = ng.fileio.bruker.read_pdata(processed_data_dir)  # processing data

    try:
        with open(os.path.join(processed_data_dir, "title"), "r") as f:
            topspin_title = f.read()
    except FileNotFoundError:
        topspin_title = None

    if len(p_data.shape) > 1:
        print("data is more than one dimensional - read failed")
        return None, a_dic, topspin_title, p_data.shape

    nscans = a_dic["acqus"]["NS"]

    # create a unit convertor to get the x-axis in ppm units
    udic = ng.bruker.guess_udic(p_dic, p_data)
    uc = ng.fileiobase.uc_from_udic(udic)

    ppm_scale = uc.ppm_scale()
    hz_scale = uc.hz_scale()

    df = pd.DataFrame(
        {
            "ppm": ppm_scale,
            "hz": hz_scale,
            "intensity": p_data,
            "intensity_per_scan": p_data / nscans,
        }
    )
    if sample_mass_mg:
        df["intensity_per_scan_per_gram"] = df["intensity_per_scan"] / sample_mass_mg * 1000.0

    if verbose:
        print(f"reading bruker data file. {udic[0]['label']} 1D spectrum, {nscans} scans.")
        if sample_mass_mg:
            print(
                f'sample mass was provided: {sample_mass_mg:f} mg. "intensity_per_scan_per_gram" column included. '
            )
        if topspin_title:
            print("\nTitle:\n")
            print(topspin_title)
        else:
            print("No title found in scan")

    return df, a_dic, topspin_title, a_data.shape


def read_topspin_txt(filename, sample_mass_mg=None, nscans=None):

    MAX_HEADER_LINES = 10
    LEFTRIGHT_REGEX = r"# LEFT = (-?\d+\.\d+) ppm. RIGHT = (-?\d+\.\d+) ppm\."
    SIZE_REGEX = r"SIZE = (\d+)"

    with open(filename, "r") as f:
        header = "".join(itertools.islice(f, MAX_HEADER_LINES))  # read the first 10 lines
    # print(header)

    leftright_match = re.search(LEFTRIGHT_REGEX, header)
    if not leftright_match:
        raise ValueError("Header improperly formatted. Could not find LEFT and/or RIGHT values")
    left = float(leftright_match.group(1))
    right = float(leftright_match.group(2))

    size_match = re.search(SIZE_REGEX, header)
    if not size_match:
        raise ValueError("Header improperly formatter. Could not find SIZE value")
    size = int(size_match.group(1))

    intensity = np.genfromtxt(filename, comments="#")
    assert len(intensity) == size, "length of intensities does not match I"

    data = {
        "ppm": np.linspace(left, right, size),
        "intensity": intensity,
        "I_norm": (intensity - intensity.min()) / (intensity.max() - intensity.min()),
    }

    if sample_mass_mg and nscans:
        data["I_per_g_per_scan"] = intensity / float(sample_mass_mg) / float(nscans) * 1000

    df = pd.DataFrame(data)
    return df


######################################################################################
# Functions for analyzing NMR data files
######################################################################################


def integrate_1d(
    data,
    process_number=1,
    sample_mass_mg=None,
    left=None,
    right=None,
    plot=False,
    verbose=False,
):
    intensity_cols = ["intensity", "intensity_per_scan", "intensity_per_scan_per_gram"]
    df = read_bruker_1d(
        data, process_number=process_number, sample_mass_mg=sample_mass_mg, verbose=verbose
    )
    if left:
        df = df[df.ppm >= left]
    if right:
        df = df[df.ppm <= right]

    if plot:
        plt.plot(df.ppm, df.intensity, "-")
        plt.plot([left, right], [0, 0], "k-", zorder=-1)
        plt.xlim(left, right)
        plt.show()

    integrated_intensities = pd.Series()
    for c in intensity_cols:
        if c not in df:
            integrated_intensities[c] = None
            continue
        integrated_intensities[c] = -1 * integrate.trapz(df[c], df.ppm)

    return integrated_intensities
