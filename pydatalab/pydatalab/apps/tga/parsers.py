import datetime
from pathlib import Path
from typing import Dict, Union

import pandas as pd

__all__ = "parse_ms_ascii"


def parse_ms_ascii(path: Path) -> Dict[str, Union[pd.DataFrame, Dict]]:
    """Parses an .asc file containing MS results and returns a dictionary with keys
    `data` and `meta`, which themselves contain a dictionary of dataframes
    for each species with the species names as keys, and a dictionary of
    metadata fields respectively.

    Parameters:
        path: The path of the file to parse.

    """

    header_keys = ("Sourcefile", "Exporttime", "Start Time", "End Time")
    data_keys = ("Time", "Time Relative [s]", "Partial Pressure [mbar]")
    header = {}
    species = []

    if not path.exists():
        raise RuntimeError(f"Provided path does not exist: {path!r}")

    with open(path, "r") as f:

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
            header[key] = datetime.datetime.strptime(header[key], "%d/%m/%Y %H:%M:%S")  # type: ignore

        reads = 0
        max_species_lines = 2
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

        # Read data with duplicated keys
        df = pd.read_csv(f, sep="\t", header=0, parse_dates=False)
        ms_results = {}
        ms_results["meta"] = header
        ms_results["data"] = {}

        for ind, specie in enumerate(species):
            species_data_keys = [k + f"{'.' + str(ind) if ind != 0 else ''}" for k in data_keys]
            ms_results["data"][specie] = df[species_data_keys].rename(
                {mangled: original for mangled, original in zip(species_data_keys, data_keys)},
                axis="columns",
            )
            ms_results["data"][specie]["Time"] = pd.to_datetime(  # type: ignore
                ms_results["data"][specie]["Time"]  # type: ignore
            )

        return ms_results
