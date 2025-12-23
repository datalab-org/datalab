"""This module contains utility functions that can be used
anywhere in the package.

"""

import datetime
import re
from json import JSONEncoder
from math import ceil

import pandas as pd
from bson import ObjectId
from flask.json.provider import DefaultJSONProvider

__all__ = ("reduce_df_size", "CustomJSONEncoder", "BSONProvider", "generate_unique_labels")


def reduce_df_size(df: pd.DataFrame, target_nrows: int, endpoint: bool = True) -> pd.DataFrame:
    """Reduce the dataframe to the number of target rows by applying a stride.

    Parameters:
        df: The dataframe to reduce.
        target_nrows: The target number of rows to reduce each column to.
        endpoint: Whether to include the endpoint of the dataframe.

    Returns:
        A copy of the input dataframe with the applied stride.

    """
    num_rows = len(df)
    stride = ceil(num_rows / target_nrows)
    if endpoint:
        indices = [0] + list(range(stride, num_rows - 1, stride)) + [num_rows - 1]
    else:
        indices = list(range(0, num_rows, stride))

    return df.iloc[indices].copy()


class CustomJSONEncoder(JSONEncoder):
    """A custom JSON encoder that uses isoformat datetime strings and
    BSON for other serialization."""

    @staticmethod
    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

        elif isinstance(o, ObjectId):
            return str(o)

        raise RuntimeError(f"Type {type(o)} not serializable")


class BSONProvider(DefaultJSONProvider):
    """A custom JSON provider that uses isoformat datetime strings and
    BSON for other serialization."""

    @staticmethod
    def default(o):
        return CustomJSONEncoder.default(o)


def shrink_label(label: str | None, max_length: int = 15) -> str:
    """Shrink label to fit within max_length, preserving file extension."""
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
    if not filenames or len(filenames) == 1:
        return filenames if filenames else []

    common_prefix = _find_common_prefix_smart(filenames)
    common_suffix = _find_common_suffix_smart(filenames)

    extension = ""
    if all("." in f for f in filenames):
        extensions = [f.rsplit(".", 1)[1] for f in filenames]
        if len(set(extensions)) == 1:
            extension = f".{extensions[0]}"

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

    return _add_numbering_for_duplicates(labels)


def _find_common_prefix_smart(strings: list[str]) -> str:
    if not strings or len(strings) < 2:
        return ""

    prefix = _find_common_prefix(strings)

    if not prefix:
        return ""

    if prefix[-1] in ("-", "_", " ", "/", "\\"):
        return prefix

    last_sep = max(
        prefix.rfind("-"),
        prefix.rfind("_"),
        prefix.rfind(" "),
        prefix.rfind("/"),
        prefix.rfind("\\"),
    )

    if last_sep > 0:
        return prefix[: last_sep + 1]

    return ""


def _find_common_suffix_smart(strings: list[str]) -> str:
    if not strings or len(strings) < 2:
        return ""

    suffix = _find_common_suffix(strings)

    if not suffix:
        return ""

    if suffix.startswith("."):
        return ""

    if suffix[0] in ("-", "_", " ", "/", "\\"):
        return suffix

    first_sep = len(suffix)
    for sep in ("-", "_", " ", "/", "\\"):
        pos = suffix.find(sep)
        if pos != -1 and pos < first_sep:
            first_sep = pos

    if first_sep < len(suffix):
        return suffix[first_sep:]

    return ""


def _find_common_prefix(strings: list[str]) -> str:
    if not strings or len(strings) < 2:
        return ""

    min_str = min(strings)
    max_str = max(strings)

    for i, char in enumerate(min_str):
        if char != max_str[i]:
            return min_str[:i]

    return min_str


def _find_common_suffix(strings: list[str]) -> str:
    if not strings or len(strings) < 2:
        return ""

    reversed_strings = [s[::-1] for s in strings]
    common_reversed_prefix = _find_common_prefix(reversed_strings)

    return common_reversed_prefix[::-1]


def _add_numbering_for_duplicates(labels: list[str]) -> list[str]:
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
