"""Utilities for reading and processing NeXus format files.

NeXus is a common data format for neutron, X-ray, and muon science.
This module provides functions to extract numeric data from NeXus files
regardless of their internal structure.
"""

from collections.abc import Callable

import nexusformat.nexus as nx
import pandas as pd

from pydatalab.logger import LOGGER


class NeXusValidationError(ValueError):
    """Raised when a NeXus file doesn't contain the expected data structure."""

    pass


# Type alias for validator functions
# Validators should take a DataFrame and raise NeXusValidationError if invalid
NeXusValidator = Callable[[pd.DataFrame], None]

# Type alias for column mapping dictionaries
ColumnMapping = dict[str, str]


def _find_all_nxdata_groups(nxroot: nx.NXroot, skip_errors: bool = True) -> dict[str, nx.NXdata]:
    """Recursively find all NXdata groups in a NeXus file.

    Args:
        nxroot: The root NXroot object
        skip_errors: If True, skip groups that have broken links or other errors

    Returns:
        Dictionary mapping paths to NXdata groups
    """
    nxdata_groups = {}

    def _recurse(group, path=""):
        try:  # noqa: S110, BLE001 — outer guard: iterating the group itself can fail if it has a broken external link at the top level; skip the whole group
            for key, item in group.items():
                item_path = f"{path}/{key}" if path else key
                try:  # noqa: S110, BLE001 — inner guard: a single broken item should not abort the rest of the loop
                    if isinstance(item, nx.NXdata):
                        # Skip empty NXdata groups (no signal attribute and no datasets)
                        if item.attrs.get("signal") is not None or len(list(item.items())) > 0:
                            nxdata_groups[item_path] = item
                    elif isinstance(item, nx.NXgroup):
                        _recurse(item, item_path)
                except Exception:  # noqa: BLE001
                    if not skip_errors:
                        raise
        except Exception:  # noqa: BLE001
            if not skip_errors:
                raise

    _recurse(nxroot)
    return nxdata_groups


def _extract_plottable_data(
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

    # The @axes attribute lists the names of datasets used as axis coordinates.
    # It can be a list (e.g. ["tth", "energy"]) or a bare string (e.g. "tth") in
    # older/simpler files — normalise to a list so the loop below is uniform.
    axes_attr = nxdata_group.attrs.get("axes", [])
    if isinstance(axes_attr, str):
        axes_attr = [axes_attr]

    # Build the dataframe
    data_dict = {}

    # Handle multi-dimensional signal data
    # XRD data normally comes as a 1xN array, but some files have it as 2D (e.g., Nx1). Reduce to 1D by summing or averaging across extra dimensions.
    # For XRD sum is used
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

    # Extract axis data. A "." value is a NeXus placeholder meaning "no axis
    # for this dimension" and should be skipped.
    for axis_name in axes_attr:
        if axis_name and axis_name != "." and axis_name in nxdata_group:
            try:
                axis_data = nxdata_group[axis_name].nxdata

                # Some instruments store axes as bin edges rather than bin centres,
                # giving N+1 values for N signal points. Convert edges to centres
                # by averaging adjacent pairs.
                if len(axis_data) == len(signal_data) + 1:
                    axis_data = 0.5 * (axis_data[:-1] + axis_data[1:])

                if len(axis_data) == len(signal_data):
                    data_dict[axis_name] = axis_data
            except Exception:  # noqa: S110, BLE001 — skip axes with broken links rather than aborting
                if not skip_broken_links:
                    raise

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


def _extract_nexus_metadata(nxroot: nx.NXroot) -> dict[str, str | float]:
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
                except Exception:  # noqa: S112, BLE001 — try next fallback path
                    continue

    except Exception:  # noqa: S110, BLE001 — return whatever metadata was collected
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

        # Extract metadata (wavelength, instrument name, etc.) upfront so it is
        # available regardless of which data-discovery path succeeds below.
        metadata = _extract_nexus_metadata(nxroot) if extract_metadata else {}

        # --- Tier 1: explicit group ---
        # If the caller knows exactly which NXdata group they want, navigate
        # directly to it by splitting the path on "/" and walking the tree.
        # Fails hard if the path doesn't exist — the caller asked for it explicitly.
        if prefer_group:
            try:
                parts = prefer_group.split("/")
                nxdata_group = nxroot
                for part in parts:
                    nxdata_group = nxdata_group[part]
                df = _extract_plottable_data(
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

        # --- Tier 2: standard NeXus plottable_data ---
        # Well-formed NeXus files expose a .plottable_data property that points
        # to the group intended for default plotting. This is the preferred approach
        # for compliant files. The emptiness check guards against files where
        # plottable_data exists but points to an empty group.
        if hasattr(nxroot, "plottable_data") and nxroot.plottable_data is not None:
            plottable = nxroot.plottable_data
            if plottable.attrs.get("signal") is not None or len(list(plottable.items())) > 0:
                LOGGER.debug("Loading %s via tier 2 (plottable_data).", filename)
                try:
                    df = _extract_plottable_data(
                        plottable,
                        reduce_method=reduce_method,
                        skip_broken_links=skip_errors,
                        column_mapping=column_mapping,
                    )
                    if validator:
                        validator(df)
                    return (df, metadata) if extract_metadata else df
                except (ValueError, KeyError) as e:
                    # plottable_data exists but extraction/validation failed — fall
                    # through to the recursive search rather than aborting.
                    LOGGER.debug(
                        "Tier 2 (plottable_data) failed for %s: %s. Falling back to recursive search.",
                        filename,
                        e,
                    )

        # --- Tier 3: recursive search ---
        # Fallback for non-standard or older files that don't follow the
        # plottable_data convention, or where tier 2 extraction failed.
        # Walks the entire file tree and tries each NXdata group in order.
        LOGGER.debug("Loading %s via tier 3 (recursive search).", filename)
        nxdata_groups = _find_all_nxdata_groups(nxroot, skip_errors=skip_errors)

        if not nxdata_groups:
            raise RuntimeError("No NXdata groups found in the NeXus file")

        # Try each candidate in order, returning the first one that extracts
        # and validates successfully. This handles files where some NXdata groups
        # are incomplete or non-plottable but a later group is valid.
        # Track the last validation error separately — if every candidate loaded
        # successfully but failed validation, that error is more informative than
        # a generic "no usable groups" message.
        last_error: Exception | None = None
        last_validation_error: NeXusValidationError | None = None
        for group in nxdata_groups.values():
            try:
                df = _extract_plottable_data(
                    group,
                    reduce_method=reduce_method,
                    skip_broken_links=skip_errors,
                    column_mapping=column_mapping,
                )
                if validator:
                    validator(df)
                return (df, metadata) if extract_metadata else df
            except NeXusValidationError as e:
                last_validation_error = e
                continue
            except Exception as e:  # noqa: BLE001
                last_error = e
                continue

        # If we only ever saw validation failures (data was found but wrong type),
        # surface that error — it's more informative than a generic RuntimeError.
        if last_validation_error and not last_error:
            raise last_validation_error

        raise RuntimeError(
            f"No usable NXdata groups found in the NeXus file. Last error: {last_validation_error or last_error}"
        )

    except NeXusValidationError:
        # Re-raise validation errors unwrapped — they are meaningful to the caller
        # and should not be obscured by a generic RuntimeError.
        raise
    except Exception as e:
        # Wrap all other exceptions with the filename for context, since raw
        # nexusformat exceptions can be cryptic.
        raise RuntimeError(f"Failed to load Nexus file {filename}: {e}")
