from pathlib import Path

import dateutil
import pandas as pd

__all__ = ("parse_mt_mass_spec_ascii",)


def parse_mt_mass_spec_ascii(path: Path) -> dict[str, pd.DataFrame | dict]:
    """Parses an .asc file containing MS results from a Mettler-Toledo
    spectrometer and returns a dictionary with keys `data` and `meta`,
    which themselves contain a dictionary of dataframes for each species
    with the species names/masses as keys, and a dictionary of
    metadata fields respectively.

    Parameters:
        path: The path of the file to parse.

    """

    header_keys = ("Sourcefile", "Exporttime", "Start Time", "End Time")
    data_keys = ("Time Relative [s]", "Partial Pressure [mbar]", "Ion Current [A]")
    header = {}
    species = []

    if not path.exists():
        raise RuntimeError(f"Provided path does not exist: {path!r}")

    with open(path) as f:
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
            if "time" in key.lower():
                header[key] = dateutil.parser.parse(header[key])  # type: ignore

        reads = 0
        max_species_lines = 10
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

        # Read data with duplicated keys: will have (column number % number of data keys) appended to them
        # MT software also writes "---" if the value is missing, so parse these as NaNs to remove later
        df = pd.read_csv(f, sep="\t", header=0, parse_dates=False, na_values=["---"])
        ms_results: dict[str, pd.DataFrame | dict] = {}
        ms_results["meta"] = header
        ms_results["data"] = {}

        # Some files have Ion Current [A] or Partial Pressure [mbar] -- only rename those that are present
        present_keys = set(df.columns.values) & set(data_keys)
        for ind, specie in enumerate(species):
            # Loop over all species and rename the columns to remove the species name and disaggregate as a dict
            species_data_keys = [k + f"{'.' + str(ind) if ind != 0 else ''}" for k in present_keys]
            ms_results["data"][specie] = df[species_data_keys].rename(
                {mangled: original for mangled, original in zip(species_data_keys, present_keys)},
                axis="columns",
            )

            # Drop time axis as format cannot be easily inferred and data is essentially duplicated: "Start Time" in header
            # provides the timestamp of the first row
            ms_results["data"][specie].drop("Time", axis="columns", inplace=True, errors="ignore")

            # If the file was provided in an incomplete form, the final rows will be NaN, so drop them
            ms_results["data"][specie].dropna(inplace=True)

        return ms_results
