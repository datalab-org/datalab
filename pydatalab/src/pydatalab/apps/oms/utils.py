"""
Utility functions for parsing OMS (Omnistar Mass Spectrometer) files

OMS files come in three formats:
1. .csv - Manual export with headers
2. .dat - Binary live-updating format (46-byte records)
3. .exp - ASCII live-updating format (space-separated integers)

The .dat and .exp files continue updating during data acquisition and may contain
more timepoints than a manually exported CSV snapshot.
"""

import struct
from pathlib import Path

import pandas as pd


def parse_oms_dat(filepath: str | Path) -> pd.DataFrame:
    """
    Parse OMS .dat binary file

    The .dat format contains 46-byte binary records, each starting with a 'V1' marker.
    There are 7 records per timepoint (6 measured species + 1 total pressure measurement).

    File structure:
        - 46-byte records starting with 'V1' marker (2 bytes)
        - Value stored as double-precision float (8 bytes) at offset 38 from V1
        - First V1 marker starts at byte 5 in the file

    Record order per timepoint:
        0: Total pressure or reference (~1.7e-06, not in CSV export)
        1: O2 (Scan 2, mass 32)
        2: Ar (Scan 3, mass 40)
        3: CO/N2 (Scan 4, mass 28)
        4: H2 (Scan 5, mass 2)
        5: C2H2 (Scan 6, mass 26)
        6: CO2 (Scan 1, mass 44)

    Args:
        filepath: Path to .dat file

    Returns:
        DataFrame with columns:
        - Data Point: Sequential measurement index (0, 1, 2, ...)
          NOTE: .dat files do not contain timestamp information
        - CO2, O2, Ar, CO/N2, H2, C2H2: Species concentrations
        - total_pressure: Additional measurement not in CSV export

    Raises:
        ValueError: If no V1 markers found in file
    """
    filepath = Path(filepath)

    with open(filepath, "rb") as f:
        data = f.read()

    # Species mapping based on observed order in .dat file
    # The CSV header defines 6 scans, but .dat has 7 records per timepoint
    species_map = {
        0: "total_pressure",  # Not in CSV export, ~2x sum of species, ~1.7e-06
        1: "O2",  # Scan 2: mass 32
        2: "Ar",  # Scan 3: mass 40
        3: "CO/N2",  # Scan 4: mass 28
        4: "H2",  # Scan 5: mass 2
        5: "C2H2",  # Scan 6: mass 26
        6: "CO2",  # Scan 1: mass 44
    }

    records = []

    # Find first V1 marker
    first_v1 = data.find(b"V1")
    if first_v1 == -1:
        raise ValueError("No V1 markers found in .dat file")

    # Parse all records starting from first V1
    pos = first_v1
    record_num = 0

    while pos + 46 <= len(data):
        # Check for V1 marker
        if data[pos : pos + 2] != b"V1":
            break

        # Read value at offset 38 (double-precision float, 8 bytes)
        value_pos = pos + 38
        value = struct.unpack("<d", data[value_pos : value_pos + 8])[0]

        # Determine timepoint and species
        timepoint = record_num // 7
        species_idx = record_num % 7
        species = species_map.get(species_idx, f"unknown_{species_idx}")

        records.append(
            {
                "timepoint": timepoint,
                "species": species,
                "value": value,
            }
        )

        pos += 46
        record_num += 1

    # Convert to DataFrame and pivot to wide format
    df = pd.DataFrame(records)

    # Pivot to wide format (one row per timepoint, one column per species)
    pivot_df = df.pivot(index="timepoint", columns="species", values="value")

    # Reorder columns to match CSV format
    csv_column_order = ["CO2", "O2", "Ar", "CO/N2", "H2", "C2H2"]
    available_cols = [col for col in csv_column_order if col in pivot_df.columns]

    # Add total_pressure at the end if present
    if "total_pressure" in pivot_df.columns:
        result_df = pivot_df[available_cols + ["total_pressure"]]
    else:
        result_df = pivot_df[available_cols]

    result_df = result_df.reset_index()

    # .dat files don't contain real time information, so we use timepoint index
    # Column name reflects this - "Data Point" rather than "Time (s)"
    result_df["Data Point"] = result_df["timepoint"]

    # Reorder to put Data Point first
    cols = ["Data Point"] + [
        col for col in result_df.columns if col not in ["Data Point", "timepoint"]
    ]
    result_df = result_df[cols]

    return result_df


def parse_oms_exp(filepath: str | Path) -> pd.DataFrame:
    """
    Parse OMS .exp ASCII file

    The .exp format contains space-separated integer codes that update live during
    data acquisition. There are 7 values per timepoint matching the .dat structure.

    Pattern observed:
        - Repeating sequence: 105 5 X 5 5 1 114
        - X increments by 322 each timepoint
        - Purpose unclear - may be quality codes, instrument status, or encoded parameters

    Args:
        filepath: Path to .exp file

    Returns:
        DataFrame with columns:
        - timepoint: Timepoint index
        - position_0 through position_6: The 7 integer values for each timepoint

    Note:
        The exact meaning of these values is not fully documented and may require
        consultation with instrument manufacturer documentation.
    """
    filepath = Path(filepath)

    with open(filepath) as f:
        content = f.read()

    # Split by whitespace
    numbers = content.split()

    records = []
    for i, num_str in enumerate(numbers):
        try:
            value = int(num_str)
            timepoint = i // 7
            position_in_group = i % 7

            records.append(
                {
                    "timepoint": timepoint,
                    f"position_{position_in_group}": value,
                }
            )
        except ValueError:
            # Skip non-integer values
            continue

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Pivot to have one row per timepoint with columns position_0 through position_6
    if len(df) > 0:
        # Group by timepoint and aggregate
        timepoint_data: dict[int, dict[str, int]] = {}
        for _, row in df.iterrows():
            tp = row["timepoint"]
            if tp not in timepoint_data:
                timepoint_data[tp] = {}
            # Get the position column name and value
            for col in row.index:
                if col.startswith("position_"):
                    timepoint_data[tp][col] = row[col]

        # Convert to DataFrame
        result_df = pd.DataFrame.from_dict(timepoint_data, orient="index")
        result_df.index.name = "timepoint"
        result_df = result_df.reset_index()

        # Ensure position columns are in order
        position_cols = [f"position_{i}" for i in range(7) if f"position_{i}" in result_df.columns]
        result_df = result_df[["timepoint"] + position_cols]
    else:
        result_df = pd.DataFrame()

    return result_df


def parse_oms_csv(filename: str | Path, auto_detect_header: bool = True) -> pd.DataFrame:
    """
    Parse .csv OMS data from mass spectrometer

    The file consists of a header with metadata. The header size is specified
    in a line containing "header" (e.g., "header",0000000026,"lines"), normally on line 2.

    Args:
        filename: Path to the .csv file
        auto_detect_header: If True, searches first 10 lines for header size.
                           If False, assumes header size of 27 lines.

    Returns:
        OMS dataframe with time and species concentration columns.
        Includes 'Time (s)' column converted from 'ms' column.

    Raises:
        ValueError: If auto_detect_header=True and header size cannot be found
    """
    filename = Path(filename)

    if auto_detect_header:
        # Search the first 10 lines for the header size
        header_size = None
        with open(filename) as f:
            for i in range(10):
                line = f.readline()
                if not line:
                    break
                if "header" in line.lower():
                    # Parse the header size from the line
                    # Format: "header",0000000026,"lines"
                    header_parts = line.strip().split(",")
                    header_size = int(header_parts[1])
                    break

        if header_size is None:
            raise ValueError("Could not find header size information in the first 10 lines")
    else:
        header_size = 27

    # Read the data, skipping the header (+1 as header seems to appear one line lower)
    oms_data = pd.read_csv(filename, skiprows=header_size + 1)

    # Drop any unnamed columns (caused by trailing commas in the CSV)
    oms_data = oms_data.loc[:, ~oms_data.columns.str.contains("^Unnamed")]

    # Convert milliseconds to seconds
    if "ms" in oms_data.columns:
        oms_data["Time (s)"] = oms_data["ms"] / 1000.0

    return oms_data
