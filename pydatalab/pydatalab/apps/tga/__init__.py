import datetime
from typing import Dict, Union

import pandas as pd


def parse(path) -> Dict[str, Union[pd.DataFrame, Dict]]:

    header_keys = ("Sourcefile", "Exporttime", "Start Time", "End Time")
    data_keys = ("Time", "Time Relative [s]", "Partial Pressure [mbar]")
    header = {}
    species = []

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
        tga_results = {}
        tga_results["meta"] = header
        tga_results["data"] = {}

        for ind, specie in enumerate(species):
            species_data_keys = [k + f"{'.' + str(ind) if ind != 0 else ''}" for k in data_keys]
            tga_results["data"][specie] = df[species_data_keys].rename(
                {mangled: original for mangled, original in zip(species_data_keys, data_keys)},
                axis="columns",
            )
            tga_results["data"][specie]["Time"] = pd.to_datetime(  # type: ignore
                tga_results["data"][specie]["Time"]  # type: ignore
            )

        return tga_results
