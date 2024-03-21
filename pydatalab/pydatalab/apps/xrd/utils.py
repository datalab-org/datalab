import os
import re
import warnings
from typing import List, Tuple

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


def getStartEnd(s: str) -> Tuple[float, float]:
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


def getIntensities(s: str) -> List[float]:
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


def toXY(intensities: List[float], start: float, end: float) -> str:
    """Converts a given list of intensities, along with a start and end angle,
    to a string in XY format.

    """
    angles = np.linspace(start, end, num=len(intensities))
    xylines = ["{:.5f} {:.3f}\r\n".format(a, i) for a, i in zip(angles, intensities)]
    return "".join(xylines)
