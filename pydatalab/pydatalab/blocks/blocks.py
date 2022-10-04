import os
import random
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import bokeh
import numpy as np
import pandas as pd
from bson import ObjectId
from scipy.signal import medfilt

from pydatalab import xrd_utils
from pydatalab.bokeh_plots import mytheme, selectable_axes_plot
from pydatalab.file_utils import get_file_info_by_id
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo

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

    def load_pattern(self, location: str) -> Tuple[pd.DataFrame, List[str]]:

        ext = os.path.splitext(location.split("/")[-1])[-1].lower()

        if ext == ".xrdml":
            df = xrd_utils.parse_xrdml(location)

        elif ext == ".xy":
            df = pd.read_csv(location, sep=r"\s+", names=["twotheta", "intensity"])

        else:
            df = pd.read_csv(location, sep=r"\s+", names=["twotheta", "intensity", "error"])

        df = df.rename(columns={"twotheta": "2θ (°)"})
        try:
            wavelength = float(self.data["wavelength"])

            df["Q (Å⁻¹)"] = 4 * np.pi / wavelength * np.sin(np.deg2rad(df["2θ (°)"]) / 2)
            df["d (Å)"] = 2 * np.pi / df["Q (Å⁻¹)"]

        # if no wavelength (or invalid wavelength) is passed, don't convert to Q and d
        except (ValueError, ZeroDivisionError):
            pass

        df["sqrt(intensity)"] = np.sqrt(df["intensity"])
        df["log(intensity)"] = np.log10(df["intensity"])
        df["normalized intensity"] = df["intensity"] / np.max(df["intensity"])
        polyfit_deg = 15
        polyfit_baseline = np.poly1d(
            np.polyfit(df["2θ (°)"], df["normalized intensity"], deg=polyfit_deg)
        )(df["2θ (°)"])
        df["intensity - polyfit baseline"] = df["normalized intensity"] - polyfit_baseline
        df["intensity - polyfit baseline"] /= np.max(df["intensity - polyfit baseline"])
        df[f"baseline (`numpy.polyfit`, deg={polyfit_deg})"] = polyfit_baseline / np.max(
            df["intensity - polyfit baseline"]
        )

        kernel_size = 101
        median_baseline = medfilt(df["normalized intensity"], kernel_size=kernel_size)
        df["intensity - median baseline"] = df["normalized intensity"] - median_baseline
        df["intensity - median baseline"] /= np.max(df["intensity - median baseline"])
        df[
            f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})"
        ] = median_baseline / np.max(df["intensity - median baseline"])

        df.index.name = location.split("/")[-1]

        y_options = [
            "normalized intensity",
            "intensity",
            "sqrt(intensity)",
            "log(intensity)",
            "intensity - median baseline",
            f"baseline (`scipy.signal.medfilt`, kernel_size={kernel_size})",
            "intensity - polyfit baseline",
            f"baseline (`numpy.polyfit`, deg={polyfit_deg})",
        ]

        return df, y_options

    def generate_xrd_plot(self):
        file_info = None
        all_files = None
        pattern_dfs = None

        if "file_id" not in self.data:
            LOGGER.warning("XRDBlock.generate_xrd_plot(): No file set in the DataBlock")
        else:
            file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)
            ext = os.path.splitext(file_info["location"].split("/")[-1])[-1].lower()
            if ext not in self.accepted_file_extensions:
                LOGGER.warning(
                    "XRDBlock.generate_xrd_plot(): Unsupported file extension (must be one of %s), not %s",
                    self.accepted_file_extensions,
                    ext,
                )
                return

            pattern_dfs, y_options = self.load_pattern(file_info["location"])
            pattern_dfs = [pattern_dfs]

        if not file_info:

            item_info = flask_mongo.db.items.find_one(
                {"item_id": self.data["item_id"]},
            )

            all_files = [
                d
                for d in [
                    get_file_info_by_id(f, update_if_live=False)
                    for f in item_info["file_ObjectIds"]
                ]
                if any(d["name"].lower().endswith(ext) for ext in self.accepted_file_extensions)
            ]

            if not all_files:
                LOGGER.warning(
                    "XRDBlock.generate_xrd_plot(): Unsupported file extension (must be .xrdml or .xy)"
                )
                return

            pattern_dfs = []
            for f in all_files:
                pattern_df, y_options = self.load_pattern(f["location"])
                pattern_dfs.append(pattern_df)

        x_options = ["2θ (°)", "Q (Å⁻¹)", "d (Å)"]

        if pattern_dfs:
            p = selectable_axes_plot(
                pattern_dfs,
                x_options=x_options,
                y_options=y_options,
                plot_line=True,
                plot_points=True,
                point_size=3,
            )

            self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)
