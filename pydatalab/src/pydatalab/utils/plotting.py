"""Plotting utility functions for label generation and formatting.

This module provides utilities for creating readable labels for plots,
particularly when dealing with multiple files or data series that may
have long or similar names.

"""

import re

__all__ = ("generate_unique_labels", "shrink_label")


def shrink_label(label: str | None, max_length: int = 15) -> str:
    """Shrink a label to fit within a maximum length while preserving key information.

    This function intelligently shortens labels by:
    - Preserving file extensions when present
    - Stripping leading zeros from long numeric sequences
    - Truncating with ellipsis (...) to indicate shortened content
    - Maintaining as much distinguishing information as possible

    Parameters:
        label: The label string to shrink. If None or empty, returns empty string.
        max_length: Maximum length for the returned label. Defaults to 15 characters.

    Returns:
        A shortened version of the label that fits within max_length characters.
        Returns the original label if it's already within the limit.

    Examples:
        >>> shrink_label("very_long_filename.txt", max_length=15)
        "very_lon...txt"

        >>> shrink_label("file_0000001.dat", max_length=15)
        "file_1.dat"

        >>> shrink_label("short.txt", max_length=15)
        "short.txt"

    """
    if not label or len(label) <= max_length:
        return label or ""

    if "." in label:
        name, ext = label.rsplit(".", 1)
        if len(ext) < 6:
            pattern = r"(\d+)"
            match = re.search(pattern, name)
            if match:
                number = match.group(1)
                if len(number) > 4 and number.startswith("0"):
                    number_stripped = number.lstrip("0") or "0"
                    name_shortened = name[: match.start()] + number_stripped + name[match.end() :]

                    if len(name_shortened) + len(ext) + 1 <= max_length:
                        return f"{name_shortened}.{ext}"

                    number_with_ext_length = len(number_stripped) + len(ext) + 1
                    available_for_prefix = max_length - number_with_ext_length - 3
                    if available_for_prefix >= 2:
                        prefix = name[: match.start()][:available_for_prefix]
                        return f"{prefix}...{number_stripped}.{ext}"

                    if number_with_ext_length <= max_length:
                        return f"{number_stripped}.{ext}"

            available = max_length - len(ext) - 4
            if available > 3:
                return f"{name[:available]}...{ext}"
            else:
                return f"{label[:12]}..."
        else:
            return f"{label[:12]}..."
    else:
        return f"{label[:12]}..."


def generate_unique_labels(
    filenames: list[str],
    max_length: int = 15,
) -> list[str]:
    """Generate unique, readable labels from a list of filenames.

    This function creates shortened labels that emphasize the distinguishing parts
    of filenames by:
    - Identifying and removing common prefixes and suffixes
    - Preserving file extensions
    - Shrinking labels to fit within max_length
    - Adding numeric suffixes for any remaining duplicates
    - Intelligently handling leading zeros in numeric patterns

    Parameters:
        filenames: List of filename strings to generate labels from.
        max_length: Maximum length for each generated label. Defaults to 15 characters.

    Returns:
        A list of unique, shortened labels corresponding to the input filenames.
        For a single filename or empty list, returns the input unchanged.

    Examples:
        >>> generate_unique_labels(["exp_run1_final.dat", "exp_run2_final.dat"])
        ["run1.dat", "run2.dat"]

        >>> generate_unique_labels(["CIF_00000001.cif", "CIF_00000002.cif"])
        ["CIF...1.cif", "CIF...2.cif"]

        >>> generate_unique_labels(["sample_A.txt", "sample_A.txt"])
        ["sample_A.txt [01]", "sample_A.txt [02]"]

    Notes:
        - Common prefixes/suffixes are detected at word boundaries (-, _, space, /, \\)
        - File extensions are preserved when all files share the same extension
        - Duplicate labels after shortening receive [01], [02], etc. suffixes

    """
    if not filenames or len(filenames) == 1:
        return filenames if filenames else []

    # Helper function to find common prefix using min/max comparison
    def find_common_prefix(strings: list[str]) -> str:
        if not strings or len(strings) < 2:
            return ""
        min_str = min(strings)
        max_str = max(strings)
        for i, char in enumerate(min_str):
            if char != max_str[i]:
                return min_str[:i]
        return min_str

    # Find common prefix, stopping at word boundaries
    raw_prefix = find_common_prefix(filenames)
    common_prefix = ""
    if raw_prefix:
        if raw_prefix[-1] in ("-", "_", " ", "/", "\\"):
            common_prefix = raw_prefix
        else:
            last_sep = max(
                raw_prefix.rfind("-"),
                raw_prefix.rfind("_"),
                raw_prefix.rfind(" "),
                raw_prefix.rfind("/"),
                raw_prefix.rfind("\\"),
            )
            if last_sep > 0:
                common_prefix = raw_prefix[: last_sep + 1]

    # Find common suffix, stopping at word boundaries (excluding file extensions)
    reversed_strings = [s[::-1] for s in filenames]
    raw_suffix = find_common_prefix(reversed_strings)[::-1]
    common_suffix = ""
    if raw_suffix and not raw_suffix.startswith("."):
        if raw_suffix[0] in ("-", "_", " ", "/", "\\"):
            common_suffix = raw_suffix
        else:
            first_sep = len(raw_suffix)
            for sep in ("-", "_", " ", "/", "\\"):
                pos = raw_suffix.find(sep)
                if pos != -1 and pos < first_sep:
                    first_sep = pos
            if first_sep < len(raw_suffix):
                common_suffix = raw_suffix[first_sep:]

    # Determine common extension if all files share one
    extension = ""
    if all("." in f for f in filenames):
        extensions = [f.rsplit(".", 1)[1] for f in filenames]
        if len(set(extensions)) == 1:
            extension = f".{extensions[0]}"

    # Extract unique parts from each filename
    unique_parts = []
    for filename in filenames:
        start_idx = len(common_prefix)
        end_idx = len(filename) - len(common_suffix)
        unique_part = filename[start_idx:end_idx] if start_idx < end_idx else filename

        if not unique_part.strip():
            unique_part = filename

        if extension and unique_part.endswith(extension):
            unique_part = unique_part[: -len(extension)]

        unique_part_without_ext = unique_part

        if len(unique_part_without_ext) < 5 and len(filename) <= max_length:
            unique_parts.append(filename)
        else:
            if extension:
                unique_part = unique_part + extension
            unique_parts.append(unique_part)

    # Shrink labels and add context from common prefix when helpful
    labels = []
    for i, part in enumerate(unique_parts):
        shrunken = shrink_label(part, max_length)

        if "." in shrunken:
            name_part, ext_part = shrunken.rsplit(".", 1)
            if name_part.replace("0", "").isdigit() and name_part.startswith("0"):
                stripped = name_part.lstrip("0") or "0"
                if len(stripped) < 6 and common_prefix:
                    available = max_length - len(stripped) - len(ext_part) - 4
                    prefix_length = min(available, 4)
                    if prefix_length >= 2:
                        prefix_to_add = common_prefix[:prefix_length].rstrip("-_. /\\")
                        if prefix_to_add:
                            shrunken = f"{prefix_to_add}...{stripped}.{ext_part}"

        if len(shrunken) < 8 and common_prefix:
            available = max_length - len(shrunken) - 3
            prefix_length = min(available, 4)
            if prefix_length >= 2:
                prefix_to_add = common_prefix[:prefix_length].rstrip("-_. /\\")
                if prefix_to_add and "..." not in shrunken:
                    shrunken = f"{prefix_to_add}...{shrunken}"

        labels.append(shrunken)

    # Add numbering for any duplicate labels
    label_counts: dict[str, int] = {}
    for label in labels:
        label_counts[label] = label_counts.get(label, 0) + 1

    if all(count == 1 for count in label_counts.values()):
        return labels

    label_counter: dict[str, int] = {}
    numbered_labels = []
    for label in labels:
        if label_counts[label] > 1:
            label_counter[label] = label_counter.get(label, 0) + 1
            numbered_labels.append(f"{label} [{label_counter[label]:02d}]")
        else:
            numbered_labels.append(label)

    return numbered_labels
