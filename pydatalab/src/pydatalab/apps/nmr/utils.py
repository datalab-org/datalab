import itertools
import re
from pathlib import Path

import matplotlib.pyplot as plt
import nmrglue as ng
import numpy as np
import pandas as pd
from scipy import integrate


def read_bruker_1d(
    data: Path | pd.DataFrame,
    process_number: int = 1,
    verbose: bool = False,
    sample_mass_mg: float | None = None,
) -> tuple[pd.DataFrame | None, dict, str | None, tuple[int, ...]]:
    """Read a 1D bruker nmr spectrum and return it as a df.

    Parameters:
        data: The directory of the full bruker data file, or a pandas DataFrame which
            will be returned without further processing.
        process_number: The process number of the processed data you want to plot [default: 1].
        verbose: Whether to print information such as the spectrum title to stdout.
        sample_mass_mg: The (optional) sample mass. If provided, the resulting DataFrame will have a "intensity_per_scan_per_gram" column.

    Returns:
        df: A pandas DataFrame containing the spectrum data, or None if the reading failed.
        a_dic: A dictionary containing the acquisition parameters.
        topspin_title: The title of the spectrum, as stored in the topspin "title" file.
        shape: The shape of the spectrum data array.

    """

    # if df is provided, just return it as-is. This functionality is provided to make functions calling read_bruker_1d flexible by default.
    # Either the data directory or the already-processed df can always be provided with equivalent results.

    if isinstance(data, pd.DataFrame):
        if verbose:
            print("data frame provided to read_bruker_1d(). Returning it as is.")
        return data
    else:
        data_dir = Path(data)

    processed_data_dir = data_dir / "pdata" / str(process_number)

    a_dic, a_data = ng.fileio.bruker.read(str(data_dir))  # aquisition_data
    p_dic, p_data = ng.fileio.bruker.read_pdata(str(processed_data_dir))  # processing data

    topspin_title = None
    title_file = processed_data_dir / "title"
    if title_file.exists():
        topspin_title = title_file.read_text()

    if len(p_data.shape) > 1:
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


def read_jcamp_dx_1d(filename: str | Path) -> tuple[pd.DataFrame, dict, str, tuple[int, ...]]:
    """Read a 1D JCAMP-DX file and return it as a dataframe with
    any associated metadata. Developed by analogy with the Bruker reader,
    and will try to make use of some Bruker-specific parameters.

    Returns:
        df: A pandas DataFrame containing the spectrum data.
        dic: A dictionary containing the acquisition parameters.
        title: The title of the spectrum, as stored in the JCAMP-DX file.
        shape: The shape of the spectrum data array.

    """

    dic, data = ng.fileio.jcampdx.read(filename)
    udic = ng.jcampdx.guess_udic(dic, data)
    uc = ng.fileiobase.uc_from_udic(udic)

    ppm_scale = uc.ppm_scale()
    hz_scale = uc.hz_scale()

    if "$NS" in dic:
        nscans = int(dic.get("$NS")[0])
    else:
        nscans = 1
    title = dic.get("TITLE", "")

    df = pd.DataFrame(
        {
            "ppm": ppm_scale,
            "hz": hz_scale,
            "intensity": data,
            "intensity_per_scan": data / nscans,
        }
    )

    return df, dic, title, data.shape


def read_topspin_txt(filename, sample_mass_mg=None, nscans=None):
    MAX_HEADER_LINES = 10
    LEFTRIGHT_REGEX = r"# LEFT = (-?\d+\.\d+) ppm. RIGHT = (-?\d+\.\d+) ppm\."
    SIZE_REGEX = r"SIZE = (\d+)"

    with open(filename) as f:
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
    if len(intensity) != size:
        raise RuntimeError(f"length of intensities does not match I ({size}) vs ({len(intensity)})")

    data = {
        "ppm": np.linspace(left, right, size),
        "intensity": intensity,
        "I_norm": (intensity - intensity.min()) / (intensity.max() - intensity.min()),
    }

    if sample_mass_mg and nscans:
        data["I_per_g_per_scan"] = intensity / float(sample_mass_mg) / float(nscans) * 1000

    df = pd.DataFrame(data)
    return df


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
