import json
import os
import random

import bokeh
import numpy as np
import pandas as pd
from bokeh.events import DoubleTap
from bokeh.io import curdoc
from bokeh.models.callbacks import CustomJS
from bokeh.plotting import figure
from bson import ObjectId
from navani import echem as ec
from scipy.interpolate import splev, splrep
from scipy.signal import savgol_filter

import bokeh_plots
import xrd_utils
from file_utils import get_file_info_by_id
from simple_bokeh_plot import mytheme, simple_bokeh_plot

UPLOAD_PATH = "uploads"


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

    blocktype = "generic"
    description = "Generic Block"

    defaults = {
        "p_spline": 5,
        "s_spline": 5,
        "win_size_2": 101,
        "win_size_1": 1001,
        "plotmode-dqdv": False,
        "plotmode-dvdq": False,
    }  # values that are set by default if they are not supplied by the dictionary in init()

    def __init__(self, sample_id, dictionary={}, unique_id=None):
        self.block_id = (
            unique_id or generate_random_id()
        )  # this is supposed to be a unique id for use in html and the database.
        self.data = {
            "sample_id": sample_id,
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

    def to_db(self):
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""
        if "file_id" in self.data:
            dict_for_db = self.data.copy()  # gross, I know
            dict_for_db["file_id"] = ObjectId(dict_for_db["file_id"])
            return dict_for_db
        return self.data

    @classmethod
    def from_db(cls, db_entry):
        """create a block from json (dictionary) stored in a db"""
        new_block = cls(db_entry["sample_id"], db_entry)
        if "file_id" in new_block.data:
            new_block.data["file_id"] = str(new_block.data["file_id"])
        return new_block

    def to_web(self):
        """returns a json-able dictionary to render the block on the web"""
        return self.data

    @classmethod
    def from_web(cls, data):
        Block = cls(data["sample_id"])
        Block.update_from_web(data)
        return Block

    def update_from_web(self, data):
        """update the object with data received from the website. Only updates fields
        that are specified in the dictionary- other fields are left alone"""
        self.data.update(data)

        return self


class CommentBlock(DataBlock):
    blocktype = "comment"
    description = "Comment"


class ImageBlock(DataBlock):
    blocktype = "image"
    description = "Image"


class XRDBlock(DataBlock):
    blocktype = "xrd"
    description = "Powder XRD"

    def generate_xrd_plot(self):
        if "file_id" not in self.data:
            print("XRDBlock.generate_xrd_plot(): No file set in the DataBlock")
            return None
        file_info = get_file_info_by_id(self.data["file_id"], update_if_live=True)

        filename = file_info["name"]
        ext = os.path.splitext(filename)[-1].lower()

        if ext not in [".xrdml", ".xy"]:
            print(
                "XRDBlock.generate_xrd_plot(): Unsupported file extension (must be .xrdml or .xy)"
            )
            return None

        print(f"The XRD file to plot is found at: {file_info['location']}")
        if ext == ".xrdml":
            print("xrdml data received. converting to .xy")
            filename = xrd_utils.convertSinglePattern(
                file_info["location"]
            )  # should give .xrdml.xy file
            print(f"the path is now: {filename}")
        else:
            filename = os.path.join(directory, filename)

        p = simple_bokeh_plot(filename, x_label="2θ (°)", y_label="intensity (counts)")

        script, div = bokeh.embed.components(p, theme=mytheme)
        # self.data["bokeh_script"] = script.replace('<script type="text/javascript">','').replace('</script>','') # this isn't great...
        # self.data["bokeh_div"] = div
        self.data["bokeh_plot_data"] = bokeh.embed.json_item(p, theme=mytheme)

    def to_web(self):
        self.generate_xrd_plot()
        return self.data

    def to_db(self):
        return {
            key: value for (key, value) in self.data.items() if key != "bokeh_plot_data"
        }  # don't save the bokeh plot in the database
