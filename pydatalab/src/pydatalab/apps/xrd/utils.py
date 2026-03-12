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


def parse_bruker_raw(filename: str) -> pd.DataFrame:
    """Reads a Bruker RAW file and returns a pandas DataFrame with columns
    twotheta and intensity, vendored and adapted from GSAS-II.

    Parameters:
        filename: The file to read.

    Returns:
        A DataFrame with columns "twotheta" and "intensity", among others.

    """
    import os
    import struct as st

    import numpy as np

    class raw_ReaderClass:
        """This class is essentially vendored from GSAS-II, with only interface
        and cosmetic changes:

        - Permalink: https://github.com/AdvancedPhotonSource/GSAS-II/blob/b87f554c5ca767601cf6f24187645c36947f9a35/GSASII/imports/G2pwd_BrukerRAW.py
        - Copyright: 2010, UChicago Argonne, LLC, Operator of Argonne National Laboratory. All rights reserved.
        - License URL: https://github.com/AdvancedPhotonSource/GSAS-II/blob/main/LICENSE

        """

        Sample: dict = {}
        dnames: list = []
        fmtVer: str = ""

        def Read(self, fp, nbytes):
            data = fp.read(nbytes)
            if "bytes" in str(type(data)):
                data = data.decode("latin-1")
            return data

        def ContentsValidator(self, filename):
            "Look through the file for expected types of lines in a valid Bruker RAW file"
            fp = open(filename, "rb")
            head = self.Read(fp, 7)
            if "bytes" in str(type(head)):
                head = head.decode("latin-1")
            if head[:4] == "RAW ":
                self.fmtVer = "Bruker RAW ver. 1"
            elif head[:4] == "RAW2":
                self.fmtVer = "Bruker RAW ver. 2"
            elif head == "RAW1.01":
                self.fmtVer = "Bruker RAW ver. 3"
            elif head == "RAW4.00":
                self.fmtVer = "Bruker RAW ver. 4"
                pwdrscan = fp.read()
                nBanks = pwdrscan.count(b"2Theta")
                if not len(self.selections):
                    self.selections = list(range(nBanks))
                    self.numbanks = nBanks
                for i in range(nBanks):
                    self.dnames.append(os.path.basename(filename) + " scan " + (str(i)))
            else:
                self.errors = "Unexpected information in header: "
                if all([ord(c) < 128 and ord(c) != 0 for c in str(head)]):  # show only if ASCII
                    self.errors += "  " + str(head)
                else:
                    self.errors += "  (binary)"
                fp.close()
                return False
            fp.close()
            return True

        def Reader(self, filename, ParentFrame=None, **kwarg):
            "Read a Bruker RAW file"
            self.comments = []
            fp = open(filename, "rb")
            if "ver. 1" in self.fmtVer:
                raise Exception(
                    'Read of Bruker "RAW " (pre-version #) file not supported'
                )  # for now
            elif "ver. 2" in self.fmtVer:
                fp.seek(4)
                nBlock = int(st.unpack("<i", fp.read(4))[0])
                fp.seek(168)
                self.comments.append("Date/Time=" + self.Read(fp, 20))
                self.comments.append("Anode=" + self.Read(fp, 2))
                self.comments.append("Ka1=%.5f" % (st.unpack("<f", fp.read(4))[0]))
                self.comments.append("Ka2=%.5f" % (st.unpack("<f", fp.read(4))[0]))
                self.comments.append("Ka2/Ka1=%.5f" % (st.unpack("<f", fp.read(4))[0]))
                fp.seek(206)
                self.comments.append("Kb=%.5f" % (st.unpack("<f", fp.read(4))[0]))
                pos = 256
                fp.seek(pos)
                blockNum = kwarg.get("blocknum", 0)
                self.idstring = os.path.basename(filename) + " Scan " + str(blockNum)
                if blockNum <= nBlock:
                    for iBlock in range(blockNum):
                        headLen = int(st.unpack("<H", fp.read(2))[0])
                        nSteps = int(st.unpack("<H", fp.read(2))[0])
                        if iBlock + 1 == blockNum:
                            fp.seek(pos + 12)
                            step = st.unpack("<f", fp.read(4))[0]
                            start2Th = st.unpack("<f", fp.read(4))[0]
                            pos += headLen  # position at start of data block
                            fp.seek(pos)
                            x = np.array([start2Th + i * step for i in range(nSteps)])
                            y = np.array(
                                [max(1.0, st.unpack("<f", fp.read(4))[0]) for i in range(nSteps)]
                            )
                            y = np.where(y < 0.0, 1.0, y)
                            w = 1.0 / y
                            self.powderdata = [
                                x,
                                y,
                                w,
                                np.zeros(nSteps),
                                np.zeros(nSteps),
                                np.zeros(nSteps),
                            ]
                            break
                        pos += headLen + 4 * nSteps
                        fp.seek(pos)
                    if blockNum == nBlock:
                        self.repeat = False
                    else:
                        self.repeat = True
                fp.close()
            elif "ver. 3" in self.fmtVer:
                fp.seek(12)
                nBlock = int(st.unpack("<i", fp.read(4))[0])
                self.comments.append("Date=" + self.Read(fp, 10))
                self.comments.append("Time=" + self.Read(fp, 10))
                fp.seek(326)
                self.comments.append("Sample=" + self.Read(fp, 60))
                fp.seek(564)
                radius = st.unpack("<f", fp.read(4))[0]
                self.comments.append("Gonio. radius=%.2f" % (radius))
                self.Sample["Gonio. radius"] = radius
                fp.seek(608)
                self.comments.append("Anode=" + self.Read(fp, 4))
                fp.seek(616)
                self.comments.append("Ka mean=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                self.comments.append("Ka1=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                self.comments.append("Ka2=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                self.comments.append("Kb=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                self.comments.append("Ka2/Ka1=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                pos = 712
                fp.seek(pos)  # position at 1st block header
                blockNum = kwarg.get("blocknum", 0)
                self.idstring = os.path.basename(filename) + " Scan " + str(blockNum)
                if blockNum <= nBlock:
                    for iBlock in range(blockNum):
                        headLen = int(st.unpack("<i", fp.read(4))[0])
                        nSteps = int(st.unpack("<i", fp.read(4))[0])
                        if not nSteps:
                            break
                        if nBlock > 1:
                            fp.seek(pos + 256)
                            headLen += st.unpack("<i", fp.read(4))[0]
                        else:
                            headLen += 40
                        if iBlock + 1 == blockNum:
                            fp.seek(pos + 8)
                            st.unpack("<d", fp.read(8))[0]
                            start2Th = st.unpack("<d", fp.read(8))[0]
                            fp.seek(pos + 212)
                            temp = st.unpack("<f", fp.read(4))[0]
                            if temp > 0.0:
                                self.Sample["Temperature"] = temp
                            fp.seek(pos + 176)
                            step = st.unpack("<d", fp.read(8))[0]
                            pos += headLen  # position at start of data block
                            fp.seek(pos)
                            x = np.array([start2Th + i * step for i in range(nSteps)])
                            try:
                                y = np.array(
                                    [
                                        max(1.0, st.unpack("<f", fp.read(4))[0])
                                        for i in range(nSteps)
                                    ]
                                )
                            except:  # noqa
                                fp.seek(pos - 40)
                                y = np.array(
                                    [
                                        max(1.0, st.unpack("<f", fp.read(4))[0])
                                        for i in range(nSteps)
                                    ]
                                )
                            w = 1.0 / y
                            self.powderdata = [
                                x,
                                y,
                                w,
                                np.zeros(nSteps),
                                np.zeros(nSteps),
                                np.zeros(nSteps),
                            ]
                            break
                        pos += headLen + 4 * nSteps
                        fp.seek(pos)
                    if blockNum == nBlock:
                        self.repeat = False
                    else:
                        self.repeat = True
                fp.close()

            elif "ver. 4" in self.fmtVer:
                driveNo = 0
                fp.seek(12)  # ok
                self.comments.append("Date=" + self.Read(fp, 12).strip("\x00"))
                self.comments.append("Time=" + self.Read(fp, 10).strip("\x00"))
                fp.seek(61)  # start of header segments
                nBank = 0
                blockNum = kwarg.get("blocknum", 0)
                while nBank < self.numbanks:
                    while True:  # read block header
                        segtype = st.unpack("<I", fp.read(4))[0]
                        if not segtype or segtype == 160:
                            break  # done with header
                        seglen = max(st.unpack("<I", fp.read(4))[0], 8)
                        if segtype == 10:
                            fp.read(4)  # skip these
                            self.comments.append(
                                "%s=%s"
                                % (
                                    self.Read(fp, 24).strip("\x00"),
                                    self.Read(fp, seglen - 36).strip("\x00"),
                                )
                            )
                        elif segtype == 30:  # x-ray source info
                            fp.read(64)
                            self.comments.append("Ka mean=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                            self.comments.append("Ka1=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                            self.comments.append("Ka2=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                            self.comments.append("Kb=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                            self.comments.append("Ka2/Ka1=%.5f" % (st.unpack("<d", fp.read(8))[0]))
                            fp.read(4)
                            self.comments.append("Anode=" + self.Read(fp, 4).strip("\x00"))
                            fp.read(seglen - 120)
                        elif segtype == 60:
                            alignFlag = st.unpack("<I", fp.read(4))[0]
                            driveName = self.Read(fp, 24).strip("\x00")
                            fp.read(32)
                            Delt = st.unpack("<d", fp.read(8))[0]
                            fp.read(seglen - 76)
                            self.comments.append("Drive %s: align flag %d" % (driveName, alignFlag))
                            self.comments.append(f"Drive {driveName}: delta {Delt:f}")
                            driveNo += 1
                        else:
                            fp.read(seglen - 8)
                    if segtype == 0 or segtype == 160:  # read data block
                        self.idstring = self.dnames[nBank]
                        meta = {}
                        fp.read(28)
                        meta["ScanType"] = self.Read(fp, 24).strip("\x00")
                        if meta["ScanType"] not in [
                            "Locked Coupled",
                            "Unlocked Coupled",
                            "Detector Scan",
                        ]:
                            return False
                        fp.read(16)
                        startAngle = st.unpack("<d", fp.read(8))[0]
                        meta["startAngle"] = "%.4f" % startAngle
                        stepSize = st.unpack("<d", fp.read(8))[0]
                        meta["stepSize"] = "%.4f" % stepSize
                        Nsteps = st.unpack("<I", fp.read(4))[0]
                        meta["Nsteps"] = "%d" % Nsteps
                        meta["stepTime(ms)"] = st.unpack("<f", fp.read(4))[0]
                        fp.read(4)
                        meta["generatorVoltage(kV)"] = st.unpack("<f", fp.read(4))[0]
                        meta["generatorCurrent(mA)"] = st.unpack("<f", fp.read(4))[0]
                        fp.read(4)
                        meta["usedWave"] = st.unpack("<d", fp.read(8))[0]
                        fp.read(16)
                        datumSize = st.unpack("<I", fp.read(4))[0]
                        hdrSize = st.unpack("<I", fp.read(4))[0]
                        fp.read(16)
                        if meta["ScanType"] in [
                            "Locked Coupled",
                            "Unlocked Coupled",
                            "Detector Scan",
                        ]:
                            while hdrSize > 0:
                                segtype = st.unpack("<I", fp.read(4))[0]
                                seglen = max(st.unpack("<I", fp.read(4))[0], 8)
                                if segtype == 50:
                                    fp.read(4)
                                    segName = self.Read(fp, 24).strip("\x00")
                                    if segName in [
                                        "Theta",
                                        "2Theta",
                                        "Chi",
                                        "Phi",
                                        "BeamTranslation",
                                        "Z-Drive",
                                        "Divergence Slit",
                                    ]:
                                        fp.read(20)
                                        meta["start %s" % segName] = (
                                            "%.4f" % (st.unpack("<d", fp.read(8))[0])
                                        )
                                        fp.read(seglen - 64)
                                    else:
                                        fp.read(seglen - 36)
                                else:
                                    fp.read(seglen - 8)
                                hdrSize -= seglen
                            # end of reading scan header
                            pos = fp.tell()
                            fp.seek(pos - 16)
                            meta["Temperature"] = st.unpack("<f", fp.read(4))[0]
                            if (
                                meta["Temperature"] > 7.0
                            ):  # one raw4 file had int4='9999' in this place & <7K unlikely for lab data
                                self.Sample["Temperature"] = meta["Temperature"]
                            try:
                                self.Sample["Omega"] = float(meta["start Theta"])
                            except:  # noqa
                                pass
                            fp.read(12)
                            x = np.array([startAngle + i * stepSize for i in range(Nsteps)])
                            y = np.array(
                                [max(1.0, st.unpack("<f", fp.read(4))[0]) for i in range(Nsteps)]
                            )
                            w = 1.0 / y
                            if nBank == blockNum - 1:
                                self.powderdata = [
                                    x,
                                    y,
                                    w,
                                    np.zeros(Nsteps),
                                    np.zeros(Nsteps),
                                    np.zeros(Nsteps),
                                ]
                                for item in meta:
                                    self.comments.append(f"{item} = {str(meta[item])}")
                                fp.close()
                                self.repeat = True
                                if nBank == self.numbanks - 1:
                                    self.repeat = False
                                return True
                        else:
                            meta["Unknown range/scan type"] = True
                            fp.read(hdrSize)
                            fp.read(datumSize * Nsteps)
                    nBank += 1
            else:
                return False
            self.repeat = False
            return True

    reader = raw_ReaderClass()
    reader.selections = []
    reader.numbanks = 0
    if not reader.ContentsValidator(filename):
        raise RuntimeError(
            f"Failed to validate Bruker RAW file {filename}: {getattr(reader, 'errors', 'unknown error')}"
        )
    read = reader.Reader(filename, blocknum=1)
    if not read:
        raise RuntimeError(f"Failed to read Bruker RAW file {filename}.")

    return pd.DataFrame({"twotheta": reader.powderdata[0], "intensity": reader.powderdata[1]})


def parse_bruker_brml(filename: str) -> pd.DataFrame:
    """Reads a Bruker BRML file (zipped XML) and returns a pandas DataFrame with columns
    twotheta and intensity.

    Parameters:
        filename: The file to read.

    Returns:
        A DataFrame with columns "twotheta" and "intensity", among others.

    """

    from xml.etree import ElementTree as ET

    with zipfile.ZipFile(filename, "r") as zip_ref:
        # Find the first RawData XML file in the archive
        raw_data_files = sorted(
            f for f in zip_ref.namelist() if re.match(r"Experiment\d+/RawData\d+\.xml", f)
        )
        if not raw_data_files:
            raise FileNotFoundError("No RawData XML file found in the .brml archive.")

        with zip_ref.open(raw_data_files[0]) as f:
            tree = ET.fromstring(f.read().decode("utf-8"))  # noqa: S314

    # Find the DataRoute with measured data
    data_route = tree.find(".//DataRoute[@RouteFlag='Measured']")
    if data_route is None:
        data_route = tree.find(".//DataRoute")
    if data_route is None:
        raise ValueError("No DataRoute element found in the BRML raw data file.")

    # Datum CSV layout: time_per_step, unknown_flag, <axis1>, <axis2>, ..., intensity
    # Column positions are determined from the ScanAxisInfo elements.
    scan_axes = data_route.findall(".//ScanAxisInfo")
    axis_names = [ax.get("AxisId") for ax in scan_axes]

    twotheta_col = None
    for i, name in enumerate(axis_names):
        if name == "TwoTheta":
            twotheta_col = i + 2  # offset past time_per_step and flag columns
            break

    if twotheta_col is None:
        raise ValueError(f"No TwoTheta axis found in BRML scan axes (found: {axis_names}).")

    intensity_col = 2 + len(axis_names)

    eff_time = float(data_route.findtext(".//TimePerStepEffective", default="0"))

    datums = data_route.findall("Datum")
    if not datums:
        raise ValueError("No Datum elements found in the BRML raw data file.")

    twotheta = np.empty(len(datums))
    intensity = np.empty(len(datums))
    for i, datum in enumerate(datums):
        parts = datum.text.split(",")  # type: ignore[union-attr]
        twotheta[i] = float(parts[twotheta_col])
        # Normalize intensity by actual/effective time ratio (as in GSAS-II)
        time_per_step = float(parts[0])
        intensity[i] = (
            float(parts[intensity_col]) * time_per_step / eff_time
            if eff_time
            else float(parts[intensity_col])
        )

    return pd.DataFrame({"twotheta": twotheta, "intensity": intensity})
