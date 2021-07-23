import os
import re
import sys
import warnings

import numpy as np

import pandas as pd

STARTEND_REGEX = (
    r"<startPosition>(\d+\.\d+)</startPosition>\s+<endPosition>(\d+\.\d+)</endPosition>"
)
DATA_REGEX = r'<intensities unit="counts">((-?\d+ )+-?\d+)</intensities>'


def read_xrdml(fn):
    with open(fn) as f:
        s = f.read()

    start, end = get_start_end(s)
    intensities = get_intensities(s)
    angles = np.linspace(start, end, num=len(intensities))

    df = pd.DataFrame({"angles": angles, "intensities": intensities})


def convert_to_Q(two_theta, wavelength=0.414581):
    return 4 * np.pi / wavelength * np.sin(two_theta / 2 * DEGREES)


def get_start_end(s):
    """parse a given xrdml file to find the start and end 2Theta points of the scan.
    Returns a tuple of floats: (start, end)"""
    match = re.search(STARTEND_REGEX, s)
    if not match:
        print("the start and end 2theta positions were not found in the XML file")
        sys.exit(1)

    start = float(match.group(1))
    end = float(match.group(2))
    return start, end


def get_intensities(s):
    """parses an xrdml file in string form to extract the intensities. Returns a list of floats"""
    match = re.search(DATA_REGEX, s)
    if not match:
        print("the intensitites were not found in the XML file")
        sys.exit(1)
    out = [float(x) for x in match.group(1).split()]  # the intensitites as a list of integers
    return out
