"""Utilities for reading and processing NeXus format files.

NeXus is a common data format for neutron, X-ray, and muon science.
This module provides functions to extract numeric data from NeXus files
regardless of their internal structure.
"""

from collections.abc import Callable

import nexusformat.nexus as nx
import pandas as pd


class NeXusValidationError(ValueError):
    """Raised when a NeXus file doesn't contain the expected data structure."""

    pass


# Type alias for validator functions
# Validators should take a DataFrame and raise NeXusValidationError if invalid
NeXusValidator = Callable[[pd.DataFrame], None]

# Type alias for column mapping dictionaries
ColumnMapping = dict[str, str]


def find_all_nxdata_groups(nxroot: nx.NXroot, skip_errors: bool = True) -> dict[str, nx.NXdata]:
    """Recursively find all NXdata groups in a NeXus file.

    Args:
        nxroot: The root NXroot object
        skip_errors: If True, skip groups that have broken links or other errors

    Returns:
        Dictionary mapping paths to NXdata groups
    """
    nxdata_groups = {}

    def _recurse(group, path=""):
        try:
            for key, item in group.items():
                item_path = f"{path}/{key}" if path else key
                try:
                    if isinstance(item, nx.NXdata):
                        nxdata_groups[item_path] = item
                    elif isinstance(item, nx.NXgroup):
                        _recurse(item, item_path)
                except Exception:
                    if not skip_errors:
                        raise
                    # Skip this item if it has broken links or other issues
        except Exception:
            if not skip_errors:
                raise

    _recurse(nxroot)
    return nxdata_groups


def extract_plottable_data(
    nxdata_group: nx.NXdata,
    reduce_method: str = "sum",
    skip_broken_links: bool = True,
    column_mapping: ColumnMapping | None = None,
) -> pd.DataFrame:
    """Extract signal and axes data from an NXdata group.

    Args:
        nxdata_group: An NXdata group containing plottable data
        reduce_method: How to reduce multi-dimensional data to 1D:
                      "sum" (default), "mean", "first", or "last"
        skip_broken_links: If True, skip axes with broken links
        column_mapping: Optional dictionary mapping NeXus column names to desired names
                       (e.g., {'tth': 'twotheta', 'counts': 'intensity'})

    Returns:
        DataFrame with columns for axes and signal data
    """
    # Get the signal (y-axis data)
    signal_name = nxdata_group.attrs.get("signal", None)
    if signal_name is None:
        raise ValueError("No signal attribute found in NXdata group")

    try:
        signal_data = nxdata_group[signal_name].nxdata
    except Exception as e:
        raise ValueError(f"Cannot access signal data '{signal_name}': {e}")

    # Get the axes (x-axis data)
    axes_attr = nxdata_group.attrs.get("axes", [])
    if isinstance(axes_attr, str):
        axes_attr = [axes_attr]

    # Build the dataframe
    data_dict = {}

    # Handle multi-dimensional signal data
    if signal_data.ndim > 1:
        # For 2D+ data, reduce to 1D
        if reduce_method == "sum":
            signal_data = signal_data.sum(axis=tuple(range(signal_data.ndim - 1)))
        elif reduce_method == "mean":
            signal_data = signal_data.mean(axis=tuple(range(signal_data.ndim - 1)))
        elif reduce_method == "first":
            signal_data = signal_data[0] if signal_data.ndim == 2 else signal_data.flatten()
        elif reduce_method == "last":
            signal_data = signal_data[-1] if signal_data.ndim == 2 else signal_data.flatten()
        else:
            raise ValueError(
                f"Unknown reduce_method '{reduce_method}'. Use 'sum', 'mean', 'first', or 'last'."
            )

    # Extract axis data
    for axis_name in axes_attr:
        if axis_name and axis_name != "." and axis_name in nxdata_group:
            try:
                axis_data = nxdata_group[axis_name].nxdata

                # Handle bin edges (convert to centers)
                if len(axis_data) == len(signal_data) + 1:
                    axis_data = 0.5 * (axis_data[:-1] + axis_data[1:])

                if len(axis_data) == len(signal_data):
                    data_dict[axis_name] = axis_data
            except Exception:
                if not skip_broken_links:
                    raise
                # Skip this axis if it has broken links

    # Add signal data
    data_dict[signal_name] = signal_data

    df = pd.DataFrame(data_dict)

    # Apply column mapping if provided
    if column_mapping:
        # Only rename columns that exist
        rename_dict = {old: new for old, new in column_mapping.items() if old in df.columns}
        if rename_dict:
            df = df.rename(columns=rename_dict)

    return df


def list_nexus_data_groups(filename: str, skip_errors: bool = True) -> dict[str, dict]:
    """List all available NXdata groups in a NeXus file with their metadata.

    Args:
        filename: Path to the .nxs file
        skip_errors: If True, skip groups with broken links or errors

    Returns:
        Dictionary mapping group paths to metadata (signal name, axes names, dimensions)
    """
    try:
        nxroot = nx.nxload(filename)
        nxdata_groups = find_all_nxdata_groups(nxroot, skip_errors=skip_errors)

        groups_info = {}
        for path, group in nxdata_groups.items():
            signal_name = group.attrs.get("signal", "unknown")
            axes_attr = group.attrs.get("axes", [])
            if isinstance(axes_attr, str):
                axes_attr = [axes_attr]

            # Get signal shape
            try:
                if signal_name in group:
                    signal_shape = group[signal_name].shape
                else:
                    signal_shape = "unknown"
            except Exception:
                if skip_errors:
                    signal_shape = "error"
                else:
                    raise

            groups_info[path] = {
                "signal": signal_name,
                "axes": axes_attr,
                "shape": signal_shape,
            }

        return groups_info
    except Exception as e:
        raise RuntimeError(f"Failed to list NXdata groups in {filename}: {e}")


def validate_xrd_columns(df: pd.DataFrame) -> None:
    """Validate that a DataFrame contains XRD-compatible columns.

    Raises:
        NeXusValidationError: If the DataFrame doesn't have appropriate XRD columns

    Args:
        df: DataFrame to validate
    """
    # Check if we have an angle column (twotheta is expected after renaming)
    has_angle = "twotheta" in df.columns

    # Check if we have an intensity column
    has_intensity = "intensity" in df.columns

    if not has_angle or not has_intensity:
        available_cols = list(df.columns)
        raise NeXusValidationError(
            f"NeXus file does not contain XRD-compatible data. "
            f"Expected columns 'twotheta' and 'intensity', but found: {available_cols}. "
            f"This file may contain neutron TOF data or other non-XRD measurements. "
            f"Consider using a generic NeXus viewer instead of XRDBlock."
        )


# Metadata field definitions: maps output key to (path, type)
# Path is dot-separated from entry, e.g., "instrument.name" -> entry["instrument"]["name"]
# Type is "str" or "float"
# Multiple paths can be specified as a list for fallback locations
NEXUS_METADATA_FIELDS: dict[str, tuple[list[str], str]] = {
    "instrument_name": (["instrument.name"], "str"),
    "beamline": (["instrument.beamline"], "str"),
    "wavelength": (
        [
            "instrument.monochromator.wavelength",
            "instrument.source.wavelength",
            "instrument.beam.incident_wavelength",
        ],
        "float",
    ),
    "sample_name": (["sample.name"], "str"),
    "chemical_formula": (["sample.chemical_formula"], "str"),
    "temperature": (["sample.temperature"], "float"),
    "start_time": (["start_time"], "str"),
    "end_time": (["end_time"], "str"),
}


def _get_nested_value(group: nx.NXgroup, path: str):
    """Navigate a dot-separated path and return the value.

    Args:
        group: The starting NXgroup
        path: Dot-separated path like "instrument.monochromator.wavelength"

    Returns:
        The value at the path, or raises KeyError/AttributeError if not found
    """
    current = group
    for part in path.split("."):
        current = current[part]
    return current.nxdata


def _convert_value(value, value_type: str) -> str | float:
    """Convert a NeXus value to the appropriate Python type.

    Args:
        value: Raw value from NeXus file
        value_type: Either "str" or "float"

    Returns:
        Converted value
    """
    # Handle arrays - take first element
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        value = value[0]

    if value_type == "float":
        return float(value)
    else:  # str
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)


def extract_nexus_metadata(nxroot: nx.NXroot) -> dict[str, str | float]:
    """Extract common metadata from a NeXus file.

    Args:
        nxroot: The root NXroot object

    Returns:
        Dictionary containing metadata like wavelength, temperature, instrument name, etc.
        Keys will only be present if the data exists in the file.
    """
    metadata: dict[str, str | float] = {}

    try:
        # Try to access entry (most NeXus files have this structure)
        if "entry" not in nxroot:
            return metadata

        entry = nxroot["entry"]

        # Extract each metadata field
        for key, (paths, value_type) in NEXUS_METADATA_FIELDS.items():
            # Skip if already found (for fields with multiple fallback paths)
            if key in metadata:
                continue

            # Try each path until one works
            for path in paths:
                try:
                    raw_value = _get_nested_value(entry, path)
                    metadata[key] = _convert_value(raw_value, value_type)
                    break  # Stop trying paths once we find a value
                except Exception:  # noqa: S112
                    continue  # Try next path

    except Exception:  # noqa: S110
        # If anything goes wrong, just return whatever metadata we collected
        pass

    return metadata


def load_nexus_file(
    filename: str,
    prefer_group: str | None = None,
    reduce_method: str = "sum",
    skip_errors: bool = True,
    validator: NeXusValidator | None = None,
    column_mapping: ColumnMapping | None = None,
    extract_metadata: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict]:
    """Loads a Nexus file and returns plottable data as a DataFrame.

    This function automatically discovers NXdata groups in the file and extracts
    numeric data from them. It handles varying NeXus file structures.

    Args:
        filename: Path to the .nxs file
        prefer_group: Optional path to a specific NXdata group (e.g., "entry/xye")
                     If None, uses the first plottable data found
        reduce_method: How to reduce multi-dimensional data to 1D:
                      "sum" (default), "mean", "first", or "last"
        skip_errors: If True, skip groups/axes with broken links or errors
        validator: Optional validation function that takes a DataFrame and raises
                  NeXusValidationError if the data doesn't meet requirements
        column_mapping: Optional dictionary to rename columns after loading
                       (e.g., {'tth': 'twotheta', 'counts': 'intensity'})
        extract_metadata: If True, also extract and return metadata from the file
                         (wavelength, temperature, instrument name, etc.)

    Returns:
        If extract_metadata is False: DataFrame containing the signal and axes data
        If extract_metadata is True: Tuple of (DataFrame, metadata dict)

    Raises:
        RuntimeError: If the file cannot be loaded or no plottable data is found
        NeXusValidationError: If validator is provided and validation fails

    Examples:
        Load default plottable data:
        >>> df = load_nexus_file("data.nxs")

        Load specific group:
        >>> df = load_nexus_file("data.nxs", prefer_group="entry/xye")

        Load with different reduction method for 2D data:
        >>> df = load_nexus_file("data.nxs", reduce_method="mean")

        Load with custom validator and column mapping:
        >>> def my_validator(df):
        ...     if 'my_column' not in df.columns:
        ...         raise NeXusValidationError("Missing required column")
        >>> df = load_nexus_file("data.nxs", validator=my_validator,
        ...                      column_mapping={'old': 'new'})

        Load with metadata:
        >>> df, metadata = load_nexus_file("data.nxs", extract_metadata=True)
        >>> print(metadata.get('wavelength'))  # Could be None if not in file
    """
    try:
        nxroot = nx.nxload(filename)

        # Extract metadata if requested
        metadata = extract_nexus_metadata(nxroot) if extract_metadata else {}

        # Try to use preferred group if specified
        if prefer_group:
            try:
                parts = prefer_group.split("/")
                nxdata_group = nxroot
                for part in parts:
                    nxdata_group = nxdata_group[part]
                df = extract_plottable_data(
                    nxdata_group,
                    reduce_method=reduce_method,
                    skip_broken_links=skip_errors,
                    column_mapping=column_mapping,
                )
                if validator:
                    validator(df)
                return (df, metadata) if extract_metadata else df
            except (KeyError, AttributeError) as e:
                raise RuntimeError(f"Preferred group '{prefer_group}' not found: {e}")

        # Otherwise, try plottable_data first (standard NeXus approach)
        if hasattr(nxroot, "plottable_data") and nxroot.plottable_data is not None:
            df = extract_plottable_data(
                nxroot.plottable_data,
                reduce_method=reduce_method,
                skip_broken_links=skip_errors,
                column_mapping=column_mapping,
            )
            if validator:
                validator(df)
            return (df, metadata) if extract_metadata else df

        # Fall back to finding all NXdata groups
        nxdata_groups = find_all_nxdata_groups(nxroot, skip_errors=skip_errors)

        if not nxdata_groups:
            raise RuntimeError("No NXdata groups found in the NeXus file")

        # Use the first available NXdata group
        first_path = list(nxdata_groups.keys())[0]
        first_group = nxdata_groups[first_path]

        df = extract_plottable_data(
            first_group,
            reduce_method=reduce_method,
            skip_broken_links=skip_errors,
            column_mapping=column_mapping,
        )

        # Run validator if provided
        if validator:
            validator(df)

        return (df, metadata) if extract_metadata else df

    except NeXusValidationError:
        # Re-raise validation errors without wrapping
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to load Nexus file {filename}: {e}")
