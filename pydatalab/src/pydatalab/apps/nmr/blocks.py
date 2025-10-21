import os
import tempfile
import warnings
import zipfile
from pathlib import Path
from typing import Any

import bokeh.embed
import pandas as pd

from pydatalab.apps.nmr.utils import read_bruker_1d, read_jcamp_dx_1d
from pydatalab.blocks.base import DataBlock
from pydatalab.bokeh_plots import DATALAB_BOKEH_THEME, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id

BRUKER_FILE_EXTENSIONS = (".zip",)
JCAMP_FILE_EXTENSIONS = (".jdx", ".dx")


class NMRBlock(DataBlock):
    blocktype = "nmr"
    name = "NMR"
    description = "A data block for loading and visualizing 1D NMR data from Bruker projects or JCAMP-DX files."

    accepted_file_extensions = BRUKER_FILE_EXTENSIONS + JCAMP_FILE_EXTENSIONS
    processed_data: dict | None = None
    defaults = {"process number": 1}
    _supports_collections = False

    @property
    def plot_functions(self):
        return (self.generate_nmr_plot,)

    def read_bruker_nmr_data(
        self,
        filename: str | Path | None = None,
        file_info: dict | None = None,
    ) -> tuple[dict | None, dict]:
        """Loads a Bruker project from the passed or attached zip file
        and parses it into a serialized dataframe and metadata dictionary.

        Parameters:
            filename: Optional local file to use instead of the database lookup.
            file_info: Optional file information dictionary to use for the database lookup.

        Returns:
            A tuple of the dataframe (serialized as dictionary) and the metadata
                dictionary, or None if no compatible data is available.

        """
        location, name, ext = self._extract_file_info(filename, file_info)

        if ext not in (".zip",):
            raise RuntimeError(
                f"Unsupported file extension for Bruker reader: {ext.lower()} (must be one of {BRUKER_FILE_EXTENSIONS})"
            )

        # unzip to tmp directory
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a Path object for the temporary directory
            tmpdir_path = Path(tmpdirname)

            # Unzip the file to the temporary directory
            with zipfile.ZipFile(location, "r") as zip_ref:
                zip_ref.extractall(tmpdir_path)

            extracted_directory_name = tmpdir_path
            root_directory: Path | None = None
            # Check if `<name>.zip` has a matching root-level `<name>` directory.
            for c in tmpdir_path.iterdir():
                # If we already found a root directory, break and emit warning about which one will be used
                if c.name == "__MACOSX":
                    continue
                if root_directory is not None:
                    warnings.warn(
                        f"Multiple Bruker projects found in the zip file {list(tmpdir_path.iterdir())}, using {root_directory}."
                    )
                    break
                if c.is_dir():
                    root_directory = c

            if root_directory:
                extracted_directory_name = root_directory

            available_processes = sorted(
                os.listdir(os.path.join(extracted_directory_name, "pdata"))
            )

            if self.data.get("selected_process") not in available_processes:
                self.data["selected_process"] = available_processes[0]

            try:
                df, a_dic, topspin_title, processed_data_shape = read_bruker_1d(
                    extracted_directory_name,
                    process_number=self.data["selected_process"],
                    verbose=False,
                )
            except Exception as error:
                raise RuntimeError(
                    f"Unable to parse {extracted_directory_name!r} as Bruker project. Error: {error!r}"
                )

        serialized_df = df.to_dict() if (df is not None) else None

        metadata = {}
        metadata["acquisition_parameters"] = a_dic["acqus"]
        metadata["processing_parameters"] = a_dic["procs"]
        metadata["pulse_program"] = a_dic["pprog"]
        metadata["available_processes"] = available_processes
        metadata["nucleus"] = a_dic["acqus"]["NUC1"]
        metadata["carrier_frequency_MHz"] = a_dic["acqus"]["SFO1"]
        metadata["carrier_offset_Hz"] = a_dic["acqus"]["O1"]
        metadata["recycle_delay"] = a_dic["acqus"]["D"][1]
        metadata["nscans"] = a_dic["acqus"]["NS"]
        metadata["CNST31"] = a_dic["acqus"]["CNST"][31]
        metadata["processed_data_shape"] = processed_data_shape
        metadata["probe_name"] = a_dic["acqus"]["PROBHD"]
        metadata["pulse_program_name"] = a_dic["acqus"]["PULPROG"]
        metadata["topspin_title"] = topspin_title
        metadata["title"] = topspin_title

        self.data["metadata"] = metadata

        return serialized_df, metadata

    @classmethod
    def _extract_file_info(
        cls, filename: str | Path | None = None, file_info: dict | None = None
    ) -> tuple[Path, str, str]:
        if file_info:
            _filename = file_info["name"]
            location = file_info["location"]
            name, ext = os.path.splitext(_filename)
        elif filename:
            location = Path(filename)
            name = Path(filename).stem
            ext = Path(filename).suffix
        else:
            raise RuntimeError("NMR block did not receive any file information.")

        return location, name, ext.lower()

    def read_jcamp_nmr_data(
        self, filename: str | Path | None = None, file_info: dict | None = None
    ):
        location, name, ext = self._extract_file_info(filename, file_info)

        if ext not in JCAMP_FILE_EXTENSIONS:
            raise RuntimeError(
                f"Unsupported file extension for JCAMP reader: {ext} (must be one of {JCAMP_FILE_EXTENSIONS})"
            )

        df, a_dic, title, shape = read_jcamp_dx_1d(location)

        data_type = a_dic.get("DATATYPE", [])
        if len(data_type) > 1:
            warnings.warn(
                f"Found multiple data types {data_type} in JCAMP file, only using the first: {data_type[0]}"
            )

        if len(data_type) == 0:
            warnings.warn(
                "No data type found in JCAMP file, may not be able to extract data successfully."
            )

        if data_type[0] not in ("NMR SPECTRUM",):
            warnings.warn(
                f"Unsupported JCAMP-DX data type: {data_type[0]}. Expected 'NMR SPECTRUM'. Will attempt to plot regardless."
            )

        metadata: dict[str, Any] = {}
        metadata["processed_data_shape"] = shape
        metadata["title"] = title

        keys_to_scape = {
            "nucleus": ".OBSERVENUCLEUS",
            "carrier_frequency_Hz": ".OBSERVEFREQUENCY",
            "pulse_program_name": ".PULSESEQUENCE",
        }
        for key, jcamp_key in keys_to_scape.items():
            try:
                metadata[key] = a_dic[jcamp_key]
                if isinstance(metadata[key], list):
                    metadata[key] = metadata[key][0]

            except Exception as e:
                warnings.warn(
                    f"Unable to parse {key} from {jcamp_key} in JCAMP file: {a_dic.get(jcamp_key)} - {e}"
                )

        if "carrier_frequency_Hz" in metadata:
            # JCAMP field is standardized on MHz so need to convert
            metadata["carrier_frequency_Hz"] = float(metadata["carrier_frequency_Hz"]) * 1e6

        if "nucleus" in metadata:
            metadata["nucleus"] = metadata["nucleus"].replace("^", "")

        try:
            # This is a Bruker-specific extension
            metadata["nscans"] = int(a_dic["$NS"][0])
        except Exception:  # noqa
            pass

        serialized_df = df.to_dict() if (df is not None) else None
        self.data["metadata"] = metadata

        return serialized_df, metadata

    def load_nmr_data(self, file_info: dict):
        location, name, ext = self._extract_file_info(file_info=file_info)

        if ext == ".zip":
            df, metadata = self.read_bruker_nmr_data(file_info=file_info)

        elif ext in (".jdx", ".dx"):
            df, metadata = self.read_jcamp_nmr_data(file_info=file_info)

        else:
            raise RuntimeError(
                f"Unsupported file extension for NMR reader: {ext} (must be one of {self.accepted_file_extensions})"
            )

        return df

    def generate_nmr_plot(self, parse: bool = True):
        """Generate an NMR plot and store processed data for the
        data files attached to this block.

        """
        if parse:
            if not self.data.get("file_id"):
                return None

            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            name, ext = os.path.splitext(file_info["name"])

            self.processed_data = self.load_nmr_data(file_info)

        processed_data_shape = self.data.get("metadata", {}).get("processed_data_shape", [])
        if not processed_data_shape or len(processed_data_shape) > 1:
            warnings.warn(
                f"Plotting is only supported for 1D data, found {processed_data_shape}. Only metadata will be displayed."
            )
            return

        if not self.processed_data:
            self.data["bokeh_plot_data"] = None
            warnings.warn(
                "No compatible processed data available for plotting, only metadata will be displayed."
            )
            return

        df = pd.DataFrame(self.processed_data)
        df["normalized intensity"] = df.intensity / df.intensity.max()

        self.data["bokeh_plot_data"] = self.make_nmr_plot(df, self.data["metadata"])

    @classmethod
    def make_nmr_plot(cls, df: pd.DataFrame, metadata: dict[str, Any]) -> str:
        """Create a Bokeh plot for the NMR data stored in the dataframe and metadata."""
        nucleus_label = metadata.get("nucleus") or ""
        # replace numbers with superscripts
        nucleus_label = nucleus_label.translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
        df.rename(
            {
                "ppm": f"{nucleus_label} chemical shift (ppm)",
                "hz": f"{nucleus_label} chemical shift (Hz)",
                "intensity": "Intensity",
                "intensity_per_scan": "Intensity per scan",
                "normalized intensity": "Normalized intensity",
            },
            axis=1,
            inplace=True,
        )

        bokeh_layout = selectable_axes_plot(
            df,
            x_options=[
                f"{nucleus_label} chemical shift (ppm)",
                f"{nucleus_label} chemical shift (Hz)",
            ],
            y_options=[
                "Intensity",
                "Intensity per scan",
                "Normalized intensity",
            ],
            plot_line=True,
            point_size=3,
        )
        # flip x axis, per NMR convention. Note that the figure is the second element
        # of the layout in the current implementation, but this could be fragile.
        bokeh_layout.children[1].x_range.flipped = True

        return bokeh.embed.json_item(bokeh_layout, theme=DATALAB_BOKEH_THEME)
