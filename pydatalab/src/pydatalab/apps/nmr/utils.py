import itertools
import re
import tempfile
import warnings
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import nmrglue as ng
import numpy as np
import pandas as pd
from scipy import integrate


def read_bruker_1d(
    data_dir: Path,
    process_number: int = 1,
    verbose: bool = False,
    sample_mass_mg: float | None = None,
) -> tuple[pd.DataFrame | None, dict, str | None, tuple[int, ...]]:
    """Read a 1D bruker nmr spectrum and return it as a df, optionally
    converting the data to frequency domain if only time-domain data is found.

    Parameters:
        data: The directory of the full Bruker project directory.
        process_number: The process number of the processed data you want to plot [default: 1].
        verbose: Whether to print information such as the spectrum title to stdout.
        sample_mass_mg: The (optional) sample mass. If provided, the resulting DataFrame will have a "intensity_per_scan_per_gram" column.

    Returns:
        df: A pandas DataFrame containing the spectrum data, or None if the reading failed.
        a_dic: A dictionary containing the acquisition parameters.
        topspin_title: The title of the spectrum, as stored in the topspin "title" file.
        shape: The shape of the spectrum data array.

    """

    data_dir = Path(data_dir)

    processed_data_dir = data_dir / "pdata" / str(process_number)

    try:
        a_dic, a_data = ng.fileio.bruker.read(str(data_dir))  # aquisition_data
    except Exception as e:
        raise RuntimeError(f"Failed to read Bruker acquisition data from {data_dir}: {e}") from e

    try:
        p_dic, p_data = ng.fileio.bruker.read_pdata(str(processed_data_dir))  # processing data
    except Exception:
        p_dic, p_data = None, None

    topspin_title = None
    title_file = processed_data_dir / "title"
    if title_file.exists():
        topspin_title = title_file.read_text()

    if p_data is not None and len(p_data.shape) > 1:
        return None, a_dic, topspin_title, p_data.shape

    nscans = a_dic["acqus"]["NS"]

    if p_dic is None:
        # create a unit convertor to get the x-axis in ppm units
        udic = ng.bruker.guess_udic(a_dic, a_data)
        uc = ng.fileiobase.uc_from_udic(udic)
        if udic[0]["time"]:
            warnings.warn(
                "No frequency-domain data found in Bruker project. Attempting best guess at processing time-domain data with FFT and ACME autophase."
            )
            p_data = ng.bruker.remove_digital_filter(a_data, a_dic)
            p_data = ng.process.proc_base.fft(a_data)

        p_data = ng.process.proc_base.rev(p_data)
        p_data = ng.process.proc_autophase.autops(p_data, "acme")
        p_data = ng.process.proc_base.di(p_data)

    else:
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


def read_jeol_jdf_1d(
    filename: str | Path,
) -> tuple[pd.DataFrame, dict, str, tuple[int, ...], dict, int]:
    """Read a JEOL .jdf file and return it as a dataframe with
    any associated metadata, processing any unprocessed time-domain data as needed.

    Developed by analogy with the Bruker/JCAMP readers

    Returns:
        df: A pandas DataFrame containing the spectrum data.
        dic: A dictionary containing the acquisition parameters.
        title: The title of the spectrum, as stored in the JEOL .jdf file.
        data.shape: The shape of the spectrum data array.
        udic: The universal dictionary of aquisition parameters generated by nmrglue
        nscans: The number of scans as read from the dictionaries

    """

    dic, data = ng.fileio.jeol.read(filename)
    udic = ng.jeol.guess_udic(dic, data)
    uc = ng.fileiobase.uc_from_udic(udic)

    if udic[0]["time"]:
        warnings.warn(
            "No frequency-domain data found in .jdf file. Attempting best guess at processing time-domain data with FFT and ACME autophase."
        )
        data = ng.process.proc_base.fft(data)
        udic[0]["time"] = False
        udic[0]["freq"] = True

    data = ng.process.proc_base.rev(data)
    data = ng.process.proc_autophase.autops(data, "acme")
    data = ng.process.proc_base.di(data)

    ppm_scale = uc.ppm_scale()
    hz_scale = uc.hz_scale()

    if "total_scans" in dic["parameters"]:
        nscans = int(dic["parameters"].get("total_scans"))
    else:
        nscans = 1
    title = dic["header"].get("title", "")

    df = pd.DataFrame(
        {
            "ppm": ppm_scale,
            "hz": hz_scale,
            "intensity": data,
            "intensity_per_scan": data / nscans,
        }
    )

    return df, dic, title, data.shape, udic, nscans


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


def fish_for_bruker_data(
    location: Path, tmpdirname: str | None = None, max_depth: int = 5
) -> list[Path]:
    """Given a zip file containing Bruker NMR data, descend into the zip
    and find all possible Bruker data directories, returning a list of paths.

    Parameters:
        location: The path to the zip file containing the Bruker data.
        tmpdirname: An optional path to a temporary directory where the zip file will be extracted.
        max_depth: The maximum depth to recurse into the directory structure when looking for Bruker data directories.

    Returns:
        A list of paths to Bruker data directories found within the zip file.

    """
    if tmpdirname is None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            return fish_for_bruker_data(location, tmpdirname=tmpdirname, max_depth=max_depth)

    # Create a Path object for the temporary directory
    tmpdir_path = Path(tmpdirname)

    # Unzip the file to the temporary directory
    with zipfile.ZipFile(location, "r") as zip_ref:
        zip_ref.extractall(tmpdir_path)

    def _scan_dir(path: Path, depth: int = 0) -> list[Path] | None:
        if depth > max_depth:
            return None

        if path.is_dir():
            if path.name == "pdata":
                return [path.parent]

            if path.name == "__MACOSX":
                return None

            results = []
            for p in path.iterdir():
                result = _scan_dir(p, depth + 1)
                if result:
                    results.extend(result)

            return results or None

        return []

    # Recurse to max_depth and find all pdata directories
    return _scan_dir(tmpdir_path, depth=0) or []
