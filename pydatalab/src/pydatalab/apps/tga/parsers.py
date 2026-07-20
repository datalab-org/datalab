import re
from io import StringIO
from pathlib import Path

import dateutil
import pandas as pd

__all__ = ("parse_mt_mass_spec_ascii", "parse_mt_mass_spec_txt")


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
        header_end = None
        for reads in range(max_header_lines):
            line = f.readline().strip()
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

        max_species_lines = 10
        for reads in range(max_species_lines):
            line = f.readline().strip()
            if line:
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


def parse_mt_mass_spec_txt(path: Path) -> dict[str, pd.DataFrame | dict]:
    """Parses an .txt file containing results associated with a tga experiment
    The data that this parser is designed for is Differential Thermal Analysis (DTS).
    This means we assume that there is a Tr column that is only recorded when there is a reference material
    being compared against the sample. This file is from a simultaneous TGA-DTA  measurement.
    (Simultaneous Thermal Analysis, STA).
    The manual can be found here: https://www.mt.com/fr/fr/home/library/user-manuals/lab-analytical-instruments/ta-manuals.html
     Parameters:
         path: The path of the file to parse.
    """

    header_keys = ["Performed"]
    header = {}

    if not path.exists():
        raise RuntimeError(f"Provided path does not exist: {path!r}")

    with open(path, encoding="latin-1") as f:
        # Read start of file until all header keys have been found
        max_header_lines = 11

        for reads in range(max_header_lines):
            line = f.readline().strip()
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

        header["Performed"] = dateutil.parser.parse(header["Performed"])  # type: ignore
        max_names_lines = 20
        expected_data_keys = ("t[s]", "Ts[°C]", "Tr[°C]", "Value[mg]")
        line = f.readline()
        for reads in range(max_names_lines):
            next_line = f.readline()

            if line and next_line:
                name = line.strip().split()[1:]
                unit = next_line.strip().split()

                column_headers = [f"{name}{unit}" for name, unit in zip(name, unit)]
                column_headers.insert(0, "Index")

                if set(expected_data_keys) & set(column_headers) == set(expected_data_keys):
                    break
                # Move to the next line
                line = next_line
        else:
            raise ValueError(
                f"Could not find names list in lines {header_end}:{header_end + max_names_lines} lines of file."
            )

        final_lines = f.readlines()

        # Remove bottom header from the file
        max_bottom_header_lines = 11
        for index in range(1, max_bottom_header_lines):
            if re.match(r"^[\d.\s-]*\d[\d.\s-]*$", final_lines[-index]):
                final_lines = final_lines[: -(index - 1)]
                break
        else:
            raise ValueError(f"Bottom header did not end within max size:{max_bottom_header_lines}")

        csv_result = StringIO("\n".join(final_lines))
        # Read data with duplicated keys: will have (column number % number of data keys) appended to them
        # MT software also writes "---" if the value is missing, so parse these as NaNs to remove later
        df = pd.read_csv(
            csv_result,
            sep=r"\s+",
            header=None,
            parse_dates=False,
            names=column_headers,
            na_values="---",
            index_col="Index",
            engine="python",
        )

        ms_results: dict[str, pd.DataFrame | dict] = {}
        ms_results["meta"] = header
        ms_results["data"] = {}

        ms_results["data"]["tga"] = df

        return ms_results
