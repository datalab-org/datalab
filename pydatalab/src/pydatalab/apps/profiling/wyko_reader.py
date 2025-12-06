"""
Wyko ASCII Profilometer File Reader

Memory-efficient parser for Wyko .ASC profilometer data files containing
surface height (RAW_DATA) and intensity profiles.
"""

from pathlib import Path
from typing import cast

import numpy as np


def parse_wyko_header(filepath: str | Path) -> dict[str, int | float | None]:
    """
    Parse Wyko ASC file header to extract metadata.

    Args:
        filepath: Path to the .ASC file

    Returns:
        Dictionary containing:
        - x_size: Number of X pixels
        - y_size: Number of Y pixels
        - pixel_size: Physical pixel size in mm
        - raw_data_start: Line number (1-indexed) where RAW_DATA begins
        - intensity_start: Line number (1-indexed) where Intensity begins (if present)

    Note: All line numbers are 1-indexed to match linecache.
    """
    metadata: dict[str, int | float | None] = {
        "x_size": None,
        "y_size": None,
        "pixel_size": None,
        "raw_data_start": None,  # 1-indexed line number
        "intensity_start": None,  # 1-indexed line number
    }

    with open(filepath) as f:
        # Use 1-indexed line counting (start=1)
        for i, line in enumerate(f, start=1):
            line_stripped = line.strip()

            if line_stripped.startswith("X Size"):
                metadata["x_size"] = int(line_stripped.split()[-1])
            elif line_stripped.startswith("Y Size"):
                metadata["y_size"] = int(line_stripped.split()[-1])
            elif line_stripped.startswith("Pixel_size"):
                parts = line_stripped.split()
                metadata["pixel_size"] = float(parts[-1])
            elif line_stripped.startswith("RAW_DATA"):
                # If "RAW_DATA" header is on line i, data starts on line i+1
                metadata["raw_data_start"] = i + 1  # 1-indexed
            # Stop after reading header (first ~10 lines)
            # Don't scan the whole file
            if i > 10:
                break

    # Calculate Intensity start position from metadata
    # Intensity block header appears after all RAW_DATA rows
    # Structure: RAW_DATA rows + 1 line for "Intensity" header
    # Note: Intensity block definition appears mid-file, not in header,
    # so we calculate its position based on X Size
    if metadata["raw_data_start"] and metadata["x_size"]:
        raw_data_start = cast(int, metadata["raw_data_start"])  # 1-indexed
        x_size = cast(int, metadata["x_size"])

        # Intensity header line = raw_data_start + x_size rows (still 1-indexed)
        intensity_header_line = raw_data_start + x_size

        # Validate that "Intensity" actually appears at the calculated line
        # linecache.getline uses 1-indexed line numbers (matches text editors)
        import linecache

        line = linecache.getline(str(filepath), intensity_header_line)
        linecache.clearcache()  # Free memory

        if line.strip().startswith("Intensity"):
            # Data starts on the line after the "Intensity" header
            metadata["intensity_start"] = intensity_header_line + 1  # 1-indexed
        else:
            # Intensity block not found at expected location
            metadata["intensity_start"] = None

    return metadata


def load_wyko_profile_pandas_chunked(
    filepath: str | Path,
    start_line: int,
    n_rows: int,
    n_cols: int,
    name: str = "Profile",
    chunksize: int = 500,
) -> np.ndarray:
    """
    Load profile using pandas with chunking - balanced speed and memory.

    This is the recommended method for loading large Wyko files.

    Args:
        filepath: Path to the .ASC file
        start_line: Line number where data starts (1-indexed)
        n_rows: Number of rows to read
        n_cols: Number of columns expected per row
        name: Name for progress display
        chunksize: Number of rows per chunk

    Returns:
        numpy array of shape (n_rows, n_cols) with float32 dtype.
    """
    import pandas as pd

    # Pre-allocate output array
    data = np.empty((n_rows, n_cols), dtype=np.float32)

    # pandas.read_csv skiprows parameter is 0-indexed (number of lines to skip)
    # Convert 1-indexed line number to 0-indexed skip count
    chunks = pd.read_csv(
        filepath,
        skiprows=start_line - 1,  # If start_line=9, skip first 8 lines
        nrows=n_rows,
        sep="\t",
        header=None,
        na_values="Bad",
        dtype=np.float32,
        engine="c",
        chunksize=chunksize,
    )

    # Track where to write each chunk in the output array (0-indexed array position)
    row_offset = 0
    for chunk in chunks:
        chunk_data = chunk.values
        chunk_rows = chunk_data.shape[0]

        # Truncate columns if needed
        if chunk_data.shape[1] > n_cols:
            chunk_data = chunk_data[:, :n_cols]

        # Write chunk to output array at current offset position
        data[row_offset : row_offset + chunk_rows, :] = chunk_data
        row_offset += chunk_rows  # Move offset forward for next chunk

    return data


def load_wyko_asc(
    filepath: str | Path, load_intensity: bool = False, progress: bool = True
) -> dict:
    """
    Load a complete Wyko ASC profilometer file using pandas chunked reading.

    This gives a good tradeoff between time and memory efficiency.

    Args:
        filepath: Path to the .ASC file
        load_intensity: If True, also load the intensity profile
        progress: If True, show progress during loading

    Returns:
        Dictionary containing:
        - metadata: Header information
        - raw_data: Height profile as numpy array (n_rows x n_cols)
        - intensity: Intensity profile (only if load_intensity=True)

    Example:
        >>> result = load_wyko_asc('sample.ASC')
        >>> height = result['raw_data']
        >>> pixel_size = result['metadata']['pixel_size']

        >>> # Plot the data
        >>> import matplotlib.pyplot as plt
        >>> plt.imshow(height, cmap='viridis')
        >>> plt.colorbar(label='Height')
        >>> plt.show()
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Parse header
    metadata = parse_wyko_header(filepath)

    if metadata["x_size"] is None or metadata["y_size"] is None:
        raise ValueError("Could not parse X Size and Y Size from file header")

    if metadata["raw_data_start"] is None:
        raise ValueError("Could not find RAW_DATA block in file")

    # Note: Data layout in file is transposed
    # Rows in file = X Size, Columns in file = Y Size
    n_rows = cast(int, metadata["x_size"])
    n_cols = cast(int, metadata["y_size"])
    raw_data_start = cast(int, metadata["raw_data_start"])

    if progress:
        print(f"Loading Wyko ASC file: {filepath.name}")
        print(f"  Dimensions: {n_rows} x {n_cols}")
        print(f"  Pixel size: {metadata['pixel_size']} mm")

    result = {"metadata": metadata}

    # Load RAW_DATA (height profile)
    result["raw_data"] = load_wyko_profile_pandas_chunked(
        filepath,
        start_line=raw_data_start,
        n_rows=n_rows,
        n_cols=n_cols,
        name="RAW_DATA",
    )

    # Optionally load Intensity
    if load_intensity:
        if metadata["intensity_start"] is None:
            raise ValueError(
                "Intensity data requested but no Intensity block found in file. "
                "The file may not contain intensity data."
            )
        intensity_start = cast(int, metadata["intensity_start"])
        result["intensity"] = load_wyko_profile_pandas_chunked(
            filepath,
            start_line=intensity_start,
            n_rows=n_rows,
            n_cols=n_cols,
            name="Intensity",
        )

    return result


def save_wyko_cache(
    filepath: str | Path, result: dict, cache_path: str | Path | None = None
) -> Path:
    """
    Save loaded Wyko data as compressed numpy file for faster reloading.

    Args:
        filepath: Original ASC file path (used to generate cache name)
        result: Result dictionary from load_wyko_asc()
        cache_path: Optional explicit path for cache file

    Returns:
        Path to the saved cache file
    """
    if cache_path is None:
        cache_path = Path(filepath).with_suffix(".npz")
    else:
        cache_path = Path(cache_path)

    save_dict = {
        "raw_data": result["raw_data"],
        "x_size": result["metadata"]["x_size"],
        "y_size": result["metadata"]["y_size"],
        "pixel_size": result["metadata"]["pixel_size"],
    }

    if "intensity" in result:
        save_dict["intensity"] = result["intensity"]

    np.savez_compressed(cache_path, **save_dict)
    print(f"Saved cache to: {cache_path}")

    return cache_path


def load_wyko_cache(cache_path: str | Path) -> dict:
    """
    Load Wyko data from a cached numpy file.

    Args:
        cache_path: Path to the .npz cache file

    Returns:
        Dictionary with same structure as load_wyko_asc()
    """
    cache_path = Path(cache_path)

    if not cache_path.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_path}")

    cached = np.load(cache_path)

    result = {
        "metadata": {
            "x_size": int(cached["x_size"]),
            "y_size": int(cached["y_size"]),
            "pixel_size": float(cached["pixel_size"]),
        },
        "raw_data": cached["raw_data"],
    }

    if "intensity" in cached:
        result["intensity"] = cached["intensity"]

    return result


# ============================================================================
# Legacy loading functions
# ============================================================================
# These are kept for reference and benchmarking, but are not actively used.
# The pandas chunked reader above provides the best speed/memory tradeoff.
# When new data files are supplied we can test if these are better suited for certain file sizes and update accordingly.


def load_wyko_profile(
    filepath: str | Path,
    start_line: int,
    n_rows: int,
    n_cols: int,
    name: str = "Profile",
    progress_interval: int = 500,
) -> np.ndarray:
    """
    LEGACY: Load a single profile from a Wyko ASC file using pure Python.

    Memory-efficient but slow. Use load_wyko_profile_pandas_chunked() instead.

    Args:
        filepath: Path to the .ASC file
        start_line: Line number where data starts (1-indexed)
        n_rows: Number of rows to read
        n_cols: Number of columns expected per row
        name: Name for progress display
        progress_interval: Print progress every N rows

    Returns:
        numpy array of shape (n_rows, n_cols) with float32 dtype.
    """
    # Pre-allocate with float32 to save memory (~50% reduction)
    data = np.empty((n_rows, n_cols), dtype=np.float32)

    with open(filepath) as f:
        # Skip to start_line (convert 1-indexed line number to 0-indexed skip count)
        # If start_line=9, we skip 8 lines to position at line 9
        for _ in range(start_line - 1):
            f.readline()

        # Read data rows
        for row_idx in range(n_rows):
            line = f.readline()
            if not line:
                print(f"Warning: Unexpected end of file at row {row_idx}")
                data[row_idx:, :] = np.nan
                break

            values = line.split()

            # Process values, handling 'Bad' markers
            col_idx = 0
            for val in values:
                if col_idx >= n_cols:
                    break
                if val == "Bad":
                    data[row_idx, col_idx] = np.nan
                else:
                    try:
                        data[row_idx, col_idx] = float(val)
                    except ValueError:
                        data[row_idx, col_idx] = np.nan
                col_idx += 1

            # Fill remaining columns with NaN if row was short
            if col_idx < n_cols:
                data[row_idx, col_idx:] = np.nan

            # Progress indicator
            if progress_interval and row_idx % progress_interval == 0:
                print(f"{name}: {row_idx}/{n_rows} rows loaded", end="\r")

    if progress_interval:
        print(f"\n{name} loaded: shape={data.shape}, dtype={data.dtype}")

    return data


def load_wyko_profile_pandas(
    filepath: str | Path,
    start_line: int,
    n_rows: int,
    n_cols: int,
    name: str = "Profile",
) -> np.ndarray:
    """
    LEGACY: Load profile using pandas without chunking.

    Fastest but uses more memory. Use load_wyko_profile_pandas_chunked() instead
    for better memory efficiency.

    Args:
        filepath: Path to the .ASC file
        start_line: Line number where data starts (1-indexed)
        n_rows: Number of rows to read
        n_cols: Number of columns expected per row
        name: Name for progress display

    Returns:
        numpy array of shape (n_rows, n_cols) with float32 dtype.
    """
    import pandas as pd

    print(f"{name}: Loading with pandas...")

    # pandas.read_csv skiprows parameter is 0-indexed (number of lines to skip)
    # Convert 1-indexed line number to 0-indexed skip count
    df = pd.read_csv(
        filepath,
        skiprows=start_line - 1,  # If start_line=9, skip first 8 lines
        nrows=n_rows,
        sep="\t",
        header=None,
        na_values="Bad",
        dtype=np.float32,
        engine="c",  # Use C parser for speed
    )

    data = df.values

    # Ensure correct shape (truncate extra columns if needed)
    if data.shape[1] > n_cols:
        data = data[:, :n_cols]

    print(f"{name} loaded: shape={data.shape}, dtype={data.dtype}")
    return data
