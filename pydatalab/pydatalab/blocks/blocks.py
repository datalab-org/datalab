import os
import random
from typing import Any, Callable, Dict, Optional, Sequence

import bokeh
import numpy as np
import pandas as pd
from bson import ObjectId

from pydatalab import xrd_utils
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

    def __init__(self, item_id, dictionary=None, unique_id=None):

        if dictionary is None:
            dictionary = {}

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
        LOGGER.debug("Initialised block %s for item ID %s.", self.__class__.__name__, item_id)

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
        new_block = cls(db_entry["item_id"], db_entry)
        if "file_id" in new_block.data:
            new_block.data["file_id"] = str(new_block.data["file_id"])
        return new_block

    def to_web(self):
        """returns a json-able dictionary to render the block on the web"""
        if self.plot_functions:
            for plot in self.plot_functions:
                plot()
        return self.data

    @classmethod
    def from_web(cls, data):
        LOGGER.debug("Loading block %s from web request.", cls.__class__.__name__)
        Block = cls(data["item_id"])
        Block.update_from_web(data)
        return Block

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


class CommentBlock(DataBlock):
    blocktype = "comment"
    description = "Comment"


class ImageBlock(DataBlock):
    blocktype = "image"
    description = "Image"
    accepted_file_extensions = (".png", ".jpeg", ".jpg")


class XRDBlock(DataBlock):
    blocktype = "xrd"
    description = "Powder XRD"
    accepted_file_extensions = (".xrdml", ".xy", ".dat", ".xye")

    defaults = {"wavelength": 1.54060}

    @property
    def plot_functions(self):
        return (self.generate_xrd_plot,)

    def generate_xrd_plot(self):
        if "file_id" not in self.data:
            LOGGER.warning("XRDBlock.generate_xrd_plot(): No file set in the DataBlock")
            return
        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

        filename = file_info["name"]
        ext = os.path.splitext(filename)[-1].lower()

        if ext not in self.accepted_file_extensions:
            LOGGER.warning(
                "XRDBlock.generate_xrd_plot(): Unsupported file extension (must be .xrdml or .xy)"
            )
            return

        if ext == ".xrdml":
            df = xrd_utils.parse_xrdml(file_info["location"])

        elif ext == ".xy":
            df = pd.read_csv(file_info["location"], sep=r"\s+", names=["twotheta", "intensity"])

        else:
            df = pd.read_csv(
                file_info["location"], sep=r"\s+", names=["twotheta", "intensity", "error"]
            )

        df = df.rename(columns={"twotheta": "2θ (°)"})
        x_options = ["2θ (°)"]
        try:
            wavelength = float(self.data["wavelength"])

            df["Q (Å⁻¹)"] = 4 * np.pi / wavelength * np.sin(np.deg2rad(df["2θ (°)"]) / 2)
            df["d (Å)"] = 2 * np.pi / df["Q (Å⁻¹)"]
            x_options += ["Q (Å⁻¹)", "d (Å)"]

        # if no wavelength (or invalid wavelength) is passed, don't convert to Q and d
        except (ValueError, ZeroDivisionError):
            pass

        df["sqrt(intensity)"] = np.sqrt(df["intensity"])
        df["log(intensity)"] = np.log10(df["intensity"])
        df["normalized intensity"] = df["intensity"] / np.max(df["intensity"])
        baseline = np.poly1d(np.polyfit(df["2θ (°)"], df["normalized intensity"], deg=10))(
            df["2θ (°)"]
        )
        df["intensity - baseline"] = df["normalized intensity"] - baseline
        df["intensity - baseline"] /= np.max(df["intensity - baseline"])
        df["baseline (NumPy poly1d, deg=10)"] = baseline / np.max(df["intensity - baseline"])

        p = selectable_axes_plot(
            df,
            x_options=x_options,
            y_options=[
                "normalized intensity",
                "intensity",
                "sqrt(intensity)",
                "log(intensity)",
                "intensity - baseline",
                "baseline (NumPy poly1d, deg=10)",
            ],
            plot_line=True,
            plot_points=False,
            point_size=3,
        )

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)
