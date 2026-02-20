import hashlib
import warnings
from pathlib import Path
from typing import Any

import bokeh
import pandas as pd
from bson import ObjectId
from navani import echem as ec
from navani.bdf import export_to_bdf

from pydatalab import bokeh_plots
from pydatalab.blocks.base import DataBlock
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo

from .utils import (
    compute_gpcl_differential,
    filter_df_by_cycle_index,
    reduce_echem_cycle_sampling,
)


class CycleBlock(DataBlock):
    """A data block for processing electrochemical cycling data.

    This class that contains functions for processing dataframes created by navani
    from raw cycler files and plotting them with Bokeh.

    Navani documentation: https://be-smith.github.io/navani/

    The file formats currently supported are:

    - Biologic (.mpr) - requires galvani https://github.com/echemdata/galvani
    - Arbin (.res, .xls and .xlsx) - the .res format requires galvani https://github.com/echemdata/galvani
    - Neware (.nda, .ndax)
    - Ivium (.txt)
    - Lanhe/Lande (.xls, .xlsx) - most formats, certain exports may not work depending on the software version or settings
    - Preprocessed (.csv) - CSV files with appropriate columns ['Capacity', 'Voltage', 'half cycle', 'full cycle', 'Current', 'state']

    """

    blocktype = "cycle"
    name = "Electrochemical cycling"
    description = """This block can plot data from electrochemical cycling experiments from many different cycler's file formats.
    The file formats currently supported are:

    - Biologic (.mpr)
    - Arbin (.res, .xls and .xlsx)
    - Neware (.nda, .ndax)
    - Ivium (.txt)
    - Lanhe/Lande (.xls, .xlsx)
    - Preprocessed (.csv) (previously extracted by navani or other tools)
    - Battery Data Format (.bdf, .bdf.csv, .bdf.parquet, .bdf.gz) - a standardized format defined by the Battery Data Alliance project (https://battery-data-alliance.github.io/battery-data-format/)

    """

    accepted_file_extensions = (
        ".mpr",
        ".txt",
        ".xls",
        ".xlsx",
        ".res",
        ".nda",
        ".ndax",
        ".csv",
        ".bdf",
        ".bdf.csv",
        ".bdf.parquet",
        ".bdf.gz",
    )

    defaults: dict[str, Any] = {
        "p_spline": 5,
        "s_spline": 5,
        "win_size_2": 101,
        "win_size_1": 1001,
        "derivative_mode": None,
    }

    def _get_characteristic_mass_g(self):
        # return {"characteristic_mass": 1000}
        doc = flask_mongo.db.items.find_one(
            {"item_id": self.data["item_id"]}, {"characteristic_mass": 1}
        )
        characteristic_mass_mg = doc.get("characteristic_mass", None)
        if characteristic_mass_mg:
            return characteristic_mass_mg / 1000.0
        return None

    def _get_file_extension(self, filename: str) -> str:
        """Determine the file extension, handling multi-part extensions like .bdf.csv.

        Raises RuntimeError if the extension is not in accepted_file_extensions.
        """
        suffixes = [s.lower() for s in Path(filename).suffixes]
        if not suffixes:
            raise RuntimeError(
                f"File {filename!r} has no extension, unable to determine file type."
            )
        if len(suffixes) >= 2 and "".join(suffixes[-2:]) in self.accepted_file_extensions:
            ext = "".join(suffixes[-2:]).lower()
        else:
            ext = suffixes[-1].lower()
        if ext not in self.accepted_file_extensions:
            raise RuntimeError(
                f"Unrecognized filetype {ext!r}, must be one of {self.accepted_file_extensions}"
            )
        return ext

    def _try_export_bdf(self, raw_df: pd.DataFrame, bdf_path: Path) -> Path | None:
        """Attempt to export a navani DataFrame to BDF format, returning the path on success or
        None on failure."""
        try:
            export_to_bdf(raw_df, save=True, filepath=bdf_path)
            return bdf_path
        except Exception as exc:
            LOGGER.warning("Failed to export BDF file: %s", exc)
            LOGGER.debug("Exception details for failed BDF export", exc_info=True)
            return None

    def _load_and_cache_echem(
        self,
        location: Path,
        bdf_path: Path | None,
        reload: bool,
        locations: list[Path] | None = None,
    ) -> tuple[pd.DataFrame, Path | None]:
        """Load echem data from file(s) with pickle and BDF caching.

        For a single file, `location` is the source file path and `locations` is None.
        For multi-file stitching, `location` is the merged cache path (used to derive the
        pickle path) and `locations` contains all source file paths to stitch.

        Parameters:
            location: Path to the source file (single) or the merged cache base path (multi).
            bdf_path: Desired path for the BDF export, or None to skip export.
            reload: If True, bypass the pickle cache and re-parse from source.
            locations: For multi-file mode, the list of all source file paths to stitch.

        Returns:
            A tuple of (raw_df, bdf_path) where bdf_path may be None if export was skipped
            or failed.
        """
        pickle_path = location.with_suffix(".RAW_PARSED.pkl")

        if not reload and pickle_path.exists():
            raw_df = pd.read_pickle(pickle_path)  # noqa: S301
            # Regenerate BDF if it was deleted or previously failed
            if bdf_path is not None and not bdf_path.exists():
                bdf_path = self._try_export_bdf(raw_df, bdf_path)
            return raw_df, bdf_path

        if locations is not None:
            # Multi-file: stitch all source files together
            try:
                LOGGER.debug("Loading multiple echem files with navani: %s", locations)
                # Suppress the navani warning when stitching files with differing capacity columns
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message=(
                            "Capacity columns are not equal, replacing with new capacity column"
                            " calculated from current and time columns and renaming the old"
                            " capacity column to Old Capacity"
                        ),
                        category=UserWarning,
                    )

                    raw_df = ec.multi_echem_file_loader([str(loc) for loc in locations])
            except Exception as exc:
                raise RuntimeError(
                    f"Navani raised an error when parsing multiple files: {exc}"
                ) from exc
        else:
            # Single file
            try:
                raw_df = ec.echem_file_loader(str(location))
            except Exception as exc:
                raise RuntimeError(f"Navani raised an error when parsing: {exc}") from exc

        raw_df.to_pickle(pickle_path)
        if bdf_path is not None:
            bdf_path = self._try_export_bdf(raw_df, bdf_path)
        return raw_df, bdf_path

    def _load_single(self, file_id: ObjectId, reload: bool) -> tuple[pd.DataFrame, Path | None]:
        """Parse a single echem file using navani, with pickle caching.

        Returns the raw DataFrame and the BDF export path (or None if the source is already BDF
        or export failed).
        """
        file_info = get_file_info_by_id(file_id, update_if_live=True)
        filename = file_info["name"]

        if file_info.get("is_live"):
            reload = True

        ext = self._get_file_extension(filename)
        location = Path(file_info["location"])
        # If the source is already BDF, no export needed (avoids e.g. file.bdf.csv -> file.bdf.csv.bdf.csv)
        bdf_path = (
            None
            if ext.startswith(".bdf")
            else location.with_name(f"{location.stem}.bdf.csv")
        )
        return self._load_and_cache_echem(location, bdf_path, reload)

    def _load_multi(
        self, file_ids: list[ObjectId], reload: bool
    ) -> tuple[pd.DataFrame, Path | None]:
        """Parse and stitch multiple echem files using navani, with pickle caching.

        Cache paths are keyed by a hash of the file IDs so different combinations
        don't collide. Cache files are saved in the same directory as the first file.
        """
        file_infos = [get_file_info_by_id(fid, update_if_live=True) for fid in file_ids]
        for info in file_infos:
            self._get_file_extension(info["name"])
        locations = [Path(info["location"]) for info in file_infos]
        cache_key = hashlib.md5(  # noqa: S324
            "|".join(sorted(str(fid) for fid in file_ids)).encode()
        ).hexdigest()[:8]
        # Cache files sit alongside the first file, named by the hash of the file ID combination
        cache_location = locations[0].parent / f"merged_{cache_key}"
        bdf_path: Path | None = cache_location.with_name(cache_location.name + ".bdf.csv")
        return self._load_and_cache_echem(cache_location, bdf_path, reload, locations=locations)

    @staticmethod
    def process_raw_echem_df(
        raw_df: pd.DataFrame, cycle_summary_df: pd.DataFrame | None
    ) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        """Filter and rename columns of a raw navani DataFrame to standardised unit-suffixed names.

        Parameters:
            raw_df: The raw DataFrame returned by navani.
            cycle_summary_df: The cycle summary DataFrame, or None if unavailable.

        Returns:
            A tuple of (raw_df, cycle_summary_df) with standardised column names.
        """
        required_keys = (
            "Time",
            "Voltage",
            "Capacity",
            "Current",
            "dqdv",
            "dvdq",
            "half cycle",
            "full cycle",
        )
        keys_with_units = {
            "Time": "time (s)",
            "Voltage": "voltage (V)",
            "Capacity": "capacity (mAh)",
            "Current": "current (mA)",
            "Charge Capacity": "charge capacity (mAh)",
            "Discharge Capacity": "discharge capacity (mAh)",
            "dqdv": "dQ/dV (mA/V)",
            "dvdq": "dV/dQ (V/mA)",
        }
        if raw_df is None:
            raise ValueError("Invalid raw_df value. Expected non-empty DataFrame.")
        raw_df = raw_df.filter(required_keys)
        raw_df.rename(columns=keys_with_units, inplace=True)
        raw_df["time (h)"] = raw_df["time (s)"] / 3600.0
        if cycle_summary_df is not None:
            cycle_summary_df.rename(columns=keys_with_units, inplace=True)
            cycle_summary_df["cycle index"] = pd.to_numeric(
                cycle_summary_df.index, downcast="integer"
            )
        return raw_df, cycle_summary_df

    def _load(self, file_ids: list[ObjectId] | ObjectId, reload: bool = True):
        """Loads the echem data using navani, summarises it, then caches the results
        to disk with suffixed names.

        Parameters:
            file_ids: The IDs of the files to load.
            reload: Whether to reload the data from the file, or use the cached version, if available.

        Returns:
            A tuple of (raw_df, cycle_summary_df, bdf_path, first_file_id) where:
                raw_df: The processed raw DataFrame with standardised column names.
                cycle_summary_df: The cycle summary DataFrame, or None if unavailable.
                bdf_path: Path to the exported BDF file, or None if export was skipped or failed.
                first_file_id: ObjectId of the first file in the file_ids list, used for constructing
                    download URLs such as /files/<first_file_id>/<bdf_path.name>.

        """

        if isinstance(file_ids, ObjectId):
            file_ids = [file_ids]

        if not isinstance(file_ids, list) or len(file_ids) == 0:
            raise ValueError("file_ids must be a non-empty list of ObjectIds.")

        first_file_id = file_ids[0]

        if len(file_ids) == 1:
            raw_df, bdf_path = self._load_single(file_ids[0], reload)
        else:
            raw_df, bdf_path = self._load_multi(file_ids, reload)

        cycle_summary_df = None
        try:
            cycle_summary_df = ec.cycle_summary(raw_df)
        except Exception as exc:
            warnings.warn(f"Cycle summary generation failed with error: {exc}")

        raw_df, cycle_summary_df = self.process_raw_echem_df(raw_df, cycle_summary_df)

        return raw_df, cycle_summary_df, bdf_path, first_file_id

    def plot_cycle(self):
        """Plots the electrochemical cycling data from the file ID provided in the request."""
        # Legacy support for when file_id was used
        if self.data.get("file_id") is not None and not self.data.get("file_ids"):
            LOGGER.info("Legacy file upload detected, using file_id")
            file_ids = [self.data["file_id"]]

        else:
            if "file_ids" not in self.data:
                LOGGER.warning("No file_ids given, skipping plot.")
                return
            if self.data["file_ids"] is None or len(self.data["file_ids"]) == 0:
                LOGGER.warning("Empty file_ids list given, skipping plot.")
                return

            file_ids = self.data["file_ids"]

        derivative_modes = (None, "dQ/dV", "dV/dQ", "final capacity")

        if self.data["derivative_mode"] not in derivative_modes:
            LOGGER.warning(
                "Invalid derivative_mode provided: %s. Expected one of %s. Falling back to `None`.",
                self.data["derivative_mode"],
                derivative_modes,
            )
            self.data["derivative_mode"] = None

        if self.data["derivative_mode"] is None:
            mode = "normal"
        else:
            mode = self.data["derivative_mode"]

        # User list input
        cycle_list = self.data.get("cyclenumber", None)
        if not isinstance(cycle_list, list):
            cycle_list = None

        raw_dfs = {}
        cycle_summary_dfs = {}

        # Single/multi mode gets a single dataframe - returned as a dict for consistency
        if self.data.get("mode") == "multi" or self.data.get("mode") == "single":
            file_info = get_file_info_by_id(file_ids[0], update_if_live=True)
            filename = file_info["name"]
            raw_df, cycle_summary_df, bdf_path, first_file_id = self._load(file_ids=file_ids)
            if bdf_path is not None and bdf_path.exists():
                self.data["bdf_url"] = f"/files/{first_file_id}/{bdf_path.name}"
            elif bdf_path is None and len(file_ids) == 1:
                # Source is already a BDF file - link directly to it
                self.data["bdf_url"] = f"/files/{first_file_id}/{filename}"
            else:
                self.data["bdf_url"] = None

            characteristic_mass_g = self._get_characteristic_mass_g()

            if characteristic_mass_g:
                raw_df["capacity (mAh/g)"] = raw_df["capacity (mAh)"] / characteristic_mass_g
                raw_df["current (mA/g)"] = raw_df["current (mA)"] / characteristic_mass_g
                if cycle_summary_df is not None:
                    cycle_summary_df["charge capacity (mAh/g)"] = (
                        cycle_summary_df["charge capacity (mAh)"] / characteristic_mass_g
                    )
                    cycle_summary_df["discharge capacity (mAh/g)"] = (
                        cycle_summary_df["discharge capacity (mAh)"] / characteristic_mass_g
                    )

            if self.data.get("mode") == "multi":
                p = Path(filename)
                filename = f"{p.stem}_merged{p.suffix}"
                raw_dfs[filename] = raw_df
                cycle_summary_dfs[filename] = cycle_summary_df
            elif self.data.get("mode") == "single":
                raw_dfs[filename] = raw_df
                cycle_summary_dfs[filename] = cycle_summary_df

        else:
            raise ValueError(f"Invalid mode {self.data.get('mode')}")

        # Load comparison files if provided
        comparison_file_ids = self.data.get("comparison_file_ids", [])
        if comparison_file_ids and len(comparison_file_ids) > 0:
            # TODO (ben smith) Currently can't load in different masses for different files in comparison mode
            for file in comparison_file_ids:
                try:
                    file_info = get_file_info_by_id(file, update_if_live=True)
                    filename = file_info["name"]
                    comparison_raw_df, comparison_cycle_summary_df, _, _ = self._load(
                        file_ids=[file], reload=False
                    )
                    # Mark comparison files with a prefix to distinguish them
                    raw_dfs[f"[Comparison] {filename}"] = comparison_raw_df
                    cycle_summary_dfs[f"[Comparison] {filename}"] = comparison_cycle_summary_df
                except Exception as exc:
                    LOGGER.error("Failed to load comparison file %s: %s", file, exc)

        dfs = {}
        for filename, raw_df in raw_dfs.items():
            cycle_summary_df = cycle_summary_dfs.get(filename)
            df = filter_df_by_cycle_index(raw_df, cycle_list)
            if cycle_summary_df is not None:
                cycle_summary_df = filter_df_by_cycle_index(cycle_summary_df, cycle_list)

            if mode in ("dQ/dV", "dV/dQ"):
                df = compute_gpcl_differential(
                    df,
                    mode=mode,
                    polynomial_spline=int(self.data["p_spline"]),
                    s_spline=10 ** (-float(self.data["s_spline"])),
                    window_size_1=int(self.data["win_size_1"]),
                    window_size_2=int(self.data["win_size_2"]),
                    use_normalized_capacity=bool(characteristic_mass_g),
                )
            # Reduce df size to 100 points per cycle by default if there are more than a 100k points
            if len(df) > 1e5:
                df = reduce_echem_cycle_sampling(df, num_samples=100)
                LOGGER.debug("Reduced df size, df length: %d", len(df))
            df["filename"] = filename
            cycle_summary_df["filename"] = filename
            dfs[filename] = df
            cycle_summary_dfs[filename] = cycle_summary_df

        # Determine plotting mode - if comparison files exist, use comparison mode
        plotting_mode = (
            "comparison"
            if comparison_file_ids and len(comparison_file_ids) > 0
            else self.data.get("mode")
        )

        layout = bokeh_plots.double_axes_echem_plot(
            dfs=list(dfs.values()),
            cycle_summary_dfs=list(cycle_summary_dfs.values()),
            mode=mode,
            normalized=bool(characteristic_mass_g),
            plotting_mode=plotting_mode,
        )

        if layout is not None:
            # Don't overwrite the previous plot data in cases where the plot is not generated
            # for a 'normal' reason
            self.data["bokeh_plot_data"] = bokeh.embed.json_item(
                layout, theme=bokeh_plots.DATALAB_BOKEH_THEME
            )
        return

    @property
    def plot_functions(self):
        return (self.plot_cycle,)
