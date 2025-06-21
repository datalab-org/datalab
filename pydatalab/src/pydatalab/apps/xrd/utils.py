import os
import re
import tempfile
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

STARTEND_REGEX = (
    r"<startPosition>(\d+\.\d+)</startPosition>\s+<endPosition>(\d+\.\d+)</endPosition>"
)
DATA_REGEX = r'<(intensities|counts) unit="counts">((-?\d+ )+-?\d+)</(intensities|counts)>'


class XrdmlParseError(Exception):
    pass


def parse_xrdml(filename: str) -> pd.DataFrame:
    """Parses an XRDML file and returns a pandas DataFrame with columns
    twotheta and intensity.

    Parameters:
        filename: The file to parse.

    """
    with open(filename) as f:
        s = f.read()

    start, end = getStartEnd(s)  # extract first and last angle
    intensities = getIntensities(s)  # extract intensities

    angles = np.linspace(start, end, num=len(intensities))

    return pd.DataFrame(
        {
            "twotheta": angles,
            "intensity": intensities,
        }
    )


def convertSinglePattern(
    filename: str,
    directory: str = ".",
    adjust_baseline: bool = False,
    overwrite: bool = False,
) -> str:
    """Converts an XRDML file to a simple xy and writes it to the passed directory, without
    overwriting any existing files.

    Parameters:
        filename: The file to convert.
        directory: The output directory.
        adjust_baseline: If True, the baseline will be adjusted so that no points are negative.
        overwrite: If True, existing files with the same filenames will be overwritten.

    Returns:
        The output filename.

    """
    filename = os.path.join(directory, filename)
    outfn = filename + ".xy"
    if os.path.exists(outfn):
        if overwrite:
            print(f"{outfn} already exists in the directory {directory}. Overwriting.")
        else:
            warnings.warn(
                f"{outfn} already exists in the directory {directory}, will not overwrite"
            )
            return outfn

    with open(filename) as f:
        s = f.read()

    print(f"Processing file {filename}")
    start, end = getStartEnd(s)
    print(f"\tstart angle: {start}\tend angle: {end}")
    intensities = getIntensities(s)

    if adjust_baseline:
        _intensities = np.array(intensities)  # type: ignore
        minI: float = np.min(_intensities)
        if minI < 0:
            print(
                f"\tadjusting baseline so that no points are negative (adding {-1 * minI} counts)"
            )
            _intensities -= minI
        else:
            print("\tno intensitites are less than zero, so no baseline adjustment performed")

        intensities = _intensities.tolist()  # type: ignore

    print(f"\tnumber of datapoints: {len(intensities)}")
    xystring = toXY(intensities, start, end)
    with open(outfn, "w") as of:
        of.write(xystring)
    print("\tSuccess!")
    return outfn


def getStartEnd(s: str) -> tuple[float, float]:
    """Parse a given string representation of an xrdml file to find the start and end 2Theta points of the scan.
    Note: this could match either Omega or 2Theta depending on their order in the XRDML file.

    Raises:
        XrdmlParseError: if the start and end positions could not be found.

    Returns:
        (start, end) positions in the XRDML file.

    """
    match = re.search(STARTEND_REGEX, s)
    if not match:
        raise XrdmlParseError("the start and end 2theta positions were not found in the XRDML file")

    start = float(match.group(1))
    end = float(match.group(2))

    return start, end


def getIntensities(s: str) -> list[float]:
    """Parse a given string representation of an xrdml file to find the peak intensities.

    Raises:
        XrdmlParseError: if intensities could not be found in the file

    Returns:
        The array of intensitites.

    """
    match = re.search(DATA_REGEX, s)
    if not match:
        raise XrdmlParseError("the intensitites were not found in the XML file")

    out = [float(x) for x in match.group(2).split()]  # the intensitites as a list of integers
    return out


def toXY(intensities: list[float], start: float, end: float) -> str:
    """Converts a given list of intensities, along with a start and end angle,
    to a string in XY format.

    """
    angles = np.linspace(start, end, num=len(intensities))
    xylines = [f"{a:.5f} {i:.3f}\r\n" for a, i in zip(angles, intensities)]
    return "".join(xylines)


def parse_rasx_zip(filename: str) -> pd.DataFrame:
    """Parses an RASX zip file and returns a pandas DataFrame with columns
    twotheta and intensity.

    Parameters:
        filename: The file to parse.

    """
    # Unzip the file to a tmp dir
    zip_path = Path(filename)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a Path object for the temporary directory
        tmpdir_path = Path(tmpdirname)

        # Unzip the file to the temporary directory
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir_path)

        # Find the .txt data file inside the unzipped .rasx archive
        # Seems to normally unzip to a folder called "Data0" with one .txt file inside
        data_file = None
        for file in tmpdir_path.glob("Data*/*.txt"):
            if data_file is not None:
                warnings.warn(f"Found other data files in .rasx archive, only using {data_file}")
                break
            data_file = file

        if data_file is None:
            raise FileNotFoundError("No .txt file found in the .rasx archive.")

        # Extract the data
        xrd_data = pd.read_csv(data_file, sep="\t", header=None)
        xrd_data.columns = ["twotheta", "intensity", "imnotsure"]

    return pd.DataFrame(
        {
            "twotheta": xrd_data["twotheta"],
            "intensity": xrd_data["intensity"],
        }
    )


def compute_cif_pxrd(filename: str, wavelength: float) -> tuple[pd.DataFrame, dict]:
    """Parses a CIF file and returns a pandas DataFrame with columns
    twotheta and intensity.

    Parameters:
        filename: The file to parse.

    """
    from matador.fingerprints.pxrd import PXRD
    from matador.scrapers.cif_scraper import cif2dict

    structure, success = cif2dict(filename)
    if not success:
        raise RuntimeError(f"Failed to parse required information from CIF file {filename}.")

    pxrd = PXRD(structure, wavelength=wavelength, two_theta_bounds=(5, 60))

    df = pd.DataFrame({"intensity": pxrd.pattern, "twotheta": pxrd.two_thetas})
    peak_data = {
        "positions": pxrd.peak_positions.tolist(),
        "intensities": pxrd.peak_intensities.tolist(),
        "widths": None,
        "hkls": pxrd.hkls.tolist(),
        "theoretical": True,
    }
    return df, peak_data
