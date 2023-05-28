import base64
import io
import os
import random
import zipfile
from typing import Any, Callable, Dict, Optional, Sequence

import bokeh.embed
import pandas as pd
from bson import ObjectId
from PIL import Image

from pydatalab import nmr_utils
from pydatalab.bokeh_plots import mytheme, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER

__all__ = ("generate_random_id", "DataBlock")


def generate_random_id():
    """This function generates a random 15-length string for use as an id for a datablock. It
    should be sufficiently random that there is a negligible risk of ever generating
    the same id twice, so this is a unique id that can be used as a unique database refrence
    and also can be used as id in the DOM. Note: uuid.uuid4() would do this too, but I think
    the generated ids are too long and ugly.

    The ids here are HTML id friendly, using lowercase letters and numbers. The first character
    is always a letter.
    """
    randlist = [random.choice("abcdefghijklmnopqrstuvwxyz")] + random.choices(
        "abcdefghijklmnopqrstuvwxyz0123456789", k=14
    )
    return "".join(randlist)


############################################################################################################
# Resources (base classes to be extended)
############################################################################################################


class DataBlock:
    """base class for a data block."""

    blocktype: str = "generic"
    description: str = "Generic Block"
    accepted_file_extensions: Sequence[str]
    # values that are set by default if they are not supplied by the dictionary in init()
    defaults: Dict[str, Any] = {}
    # values cached on the block instance for faster retrieval
    cache: Optional[Dict[str, Any]] = None
    plot_functions: Optional[Sequence[Callable[[], None]]] = None
    # whether this datablock can operate on collection data, or just individual items
    __supports_collections: bool = False

    def __init__(
        self,
        item_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        dictionary=None,
        unique_id=None,
    ):
        if dictionary is None:
            dictionary = {}

        if item_id is None and not self.__supports_collections:
            raise RuntimeError(f"Must supply `item_id` to make {self.__class__.__name__}.")

        if collection_id is not None and not self.__supports_collections:
            raise RuntimeError(
                f"This block ({self.__class__.__name__}) does not support collections."
            )

        if item_id is not None and collection_id is not None:
            raise RuntimeError("Must provide only one of `item_id` and `collection_id`.")

        # Initialise cache
        self.cache = {}

        LOGGER.debug(
            "Creating new block '%s' associated with item_id '%s'",
            self.__class__.__name__,
            item_id,
        )
        self.block_id = (
            unique_id or generate_random_id()
        )  # this is supposed to be a unique id for use in html and the database.
        self.data = {
            "item_id": item_id,
            "collection_id": collection_id,
            "blocktype": self.blocktype,
            "block_id": self.block_id,
            **self.defaults,
        }

        # convert ObjectId file_ids to string to make handling them easier when sending to and from web
        if "file_id" in self.data:
            self.data["file_id"] = str(self.data["file_id"])

        if "title" not in self.data:
            self.data["title"] = self.description
        self.data.update(
            dictionary
        )  # this could overwrite blocktype and block_id. I think that's reasonable... maybe
        LOGGER.debug(
            "Initialised block %s for item ID %s or collection ID %s.",
            self.__class__.__name__,
            item_id,
            collection_id,
        )

    def to_db(self):
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""
        LOGGER.debug("Casting block %s to database object.", self.__class__.__name__)

        if "file_id" in self.data:
            dict_for_db = self.data.copy()  # gross, I know
            dict_for_db["file_id"] = ObjectId(dict_for_db["file_id"])
            return dict_for_db

        if "bokeh_plot_data" in self.data:
            self.data.pop("bokeh_plot_data")
        return self.data

    @classmethod
    def from_db(cls, db_entry):
        """create a block from json (dictionary) stored in a db"""
        LOGGER.debug("Loading block %s from database object.", cls.__class__.__name__)
        new_block = cls(
            item_id=db_entry.get("item_id"),
            collection_id=db_entry.get("collection_id"),
            dictionary=db_entry,
        )
        if "file_id" in new_block.data:
            new_block.data["file_id"] = str(new_block.data["file_id"])
        return new_block

    def to_web(self):
        """returns a json-able dictionary to render the block on the web"""
        if self.plot_functions:
            for plot in self.plot_functions:
                try:
                    plot()
                except RuntimeError:
                    LOGGER.warning(
                        f"Could not create plot for {self.__class__.__name__}: {self.data}"
                    )
        return self.data

    @classmethod
    def from_web(cls, data):
        LOGGER.debug("Loading block %s from web request.", cls.__class__.__name__)
        block = cls(
            item_id=data.get("item_id"),
            collection_id=data.get("collection_id"),
            unique_id=data["block_id"],
        )
        block.update_from_web(data)
        return block

    def update_from_web(self, data):
        """update the object with data received from the website. Only updates fields
        that are specified in the dictionary- other fields are left alone"""
        LOGGER.debug(
            "Updating block %s from web request",
            self.__class__.__name__,
        )
        self.data.update(data)

        return self


class NotSupportedBlock(DataBlock):
    blocktype = "notsupported"
    description = "Block not supported"
    __supports_collections = True


class CommentBlock(DataBlock):
    blocktype = "comment"
    description = "Comment"
    __supports_collections = True


class MediaBlock(DataBlock):
    blocktype = "media"
    description = "Media"
    accepted_file_extensions = (".png", ".jpeg", ".jpg", ".tif", ".tiff", ".mp4", ".mov", ".webm")
    __supports_collections = False

    @property
    def plot_functions(self):
        return (self.encode_tiff,)

    def encode_tiff(self):
        if "file_id" not in self.data:
            LOGGER.warning("ImageBlock.encode_tiff(): No file set in the DataBlock")
            return
        if "b64_encoded_image" not in self.data:
            self.data["b64_encoded_image"] = {}
        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        if file_info["name"].endswith(".tif") or file_info["name"].endswith(".tiff"):
            im = Image.open(file_info["location"])
            LOGGER.warning("Making base64 encoding of tif")
            with io.BytesIO() as f:
                im.save(f, format="PNG")
                f.seek(0)
                self.data["b64_encoded_image"][self.data["file_id"]] = base64.b64encode(
                    f.getvalue()
                ).decode()


class NMRBlock(DataBlock):
    blocktype = "nmr"
    description = "Simple NMR Block"
    accepted_file_extensions = ".zip"
    defaults = {"process number": 1}
    __supports_collections = False

    @property
    def plot_functions(self):
        return (self.generate_nmr_plot,)

    def read_bruker_nmr_data(self):
        if "file_id" not in self.data:
            LOGGER.warning("NMRPlot.read_bruker_nmr_data(): No file set in the DataBlock")
            return

        zip_file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
        filename = zip_file_info["name"]

        name, ext = os.path.splitext(filename)
        if ext.lower() not in self.accepted_file_extensions:
            LOGGER.warning(
                "NMRBlock.read_bruker_nmr_data(): Unsupported file extension (must be .zip)"
            )
            return

        # unzip:
        directory_location = zip_file_info["location"] + ".extracted"
        LOGGER.debug(f"Directory location is: {directory_location}")
        with zipfile.ZipFile(zip_file_info["location"], "r") as zip_ref:
            zip_ref.extractall(directory_location)

        extracted_directory_name = os.path.join(directory_location, name)
        available_processes = os.listdir(os.path.join(extracted_directory_name, "pdata"))

        if self.data.get("selected_process") not in available_processes:
            self.data["selected_process"] = available_processes[0]

        try:
            df, a_dic, topspin_title, processed_data_shape = nmr_utils.read_bruker_1d(
                os.path.join(directory_location, name),
                process_number=self.data["selected_process"],
                verbose=False,
            )
        except Exception as error:
            LOGGER.critical(f"Unable to parse {name} as Bruker project. {error}")
            return

        serialized_df = df.to_dict() if (df is not None) else None

        # all data sorted in a fairly raw way
        self.data["processed_data"] = serialized_df
        self.data["acquisition_parameters"] = a_dic["acqus"]
        self.data["processing_parameters"] = a_dic["procs"]
        self.data["pulse_program"] = a_dic["pprog"]

        # specific things that we might want to pull out for the UI:
        self.data["available_processes"] = available_processes
        self.data["nucleus"] = a_dic["acqus"]["NUC1"]
        self.data["carrier_frequency_MHz"] = a_dic["acqus"]["SFO1"]
        self.data["carrier_offset_Hz"] = a_dic["acqus"]["O1"]
        self.data["recycle_delay"] = a_dic["acqus"]["D"][1]
        self.data["nscans"] = a_dic["acqus"]["NS"]
        self.data["CNST31"] = a_dic["acqus"]["CNST"][31]
        self.data["processed_data_shape"] = processed_data_shape

        self.data["probe_name"] = a_dic["acqus"]["PROBHD"]
        self.data["pulse_program_name"] = a_dic["acqus"]["PULPROG"]
        self.data["topspin_title"] = topspin_title

    def generate_nmr_plot(self):
        self.read_bruker_nmr_data()  # currently calls every time plotting happens, but it should only happen if the file was updated
        if "processed_data" not in self.data or not self.data["processed_data"]:
            self.data["bokeh_plot_data"] = None
            return

        df = pd.DataFrame(self.data["processed_data"])
        df["normalized intensity"] = df.intensity / df.intensity.max()

        bokeh_layout = selectable_axes_plot(
            df,
            x_options=["ppm", "hz"],
            y_options=[
                "intensity",
                "intensity_per_scan",
                "normalized intensity",
            ],
            plot_line=True,
            point_size=3,
        )
        bokeh_layout.children[0].x_range.flipped = True  # flip x axis, per NMR convention

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(bokeh_layout, theme=mytheme)
