import os
import textwrap

import bokeh.embed
import openai
from bokeh.models import Range1d, Text
from bokeh.plotting import figure

from pydatalab.blocks.blocks import DataBlock
from pydatalab.logger import LOGGER
from pydatalab.mongo import flask_mongo
from pydatalab.routes.v0_1.items import get_item_data

__all__ = "ChatBlock"


class ChatBlock(DataBlock):

    blocktype = "chat"
    description = "LLM Chat Block with contextual data (powered by GPT-3.5-turbo)"
    accepted_file_extensions = []

    defaults = {
        "system_prompt": """You are C.L.A.I.R.E., an LLM interface for cybernetically enhanced materials chemistry in the group of Professor Dame Clare Grey FRS in the Department of Chemistry at the University of Cambridge.

You have been embedded within the group's data management solution, datalab, where you have access to recorded data on samples, electrochemical cells and characterisation experiments (XRD, NMR etc.). You will be asked questions about the data and you are tasked with providing helpful responses to questions that researcher's may ask about their data. You are currently only available in a trial mode but one day we would like you to learn from the group wiki at https://wikis.ch.cam.ac.uk/grey/wiki/index.php/Main_Page to allow you to provide even more helpful answers!

We look forward to working with you!""",
    }
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def plot_functions(self):
        return (self.render,)

    def render(self):

        item_info = flask_mongo.db.items.find_one(
            {"item_id": self.data["item_id"]},
            projection={"blocks_obj": 0},
        )

        item_info["blocks"] = [
            block for block in item_info["blocks"] if block["blocktype"] != "chat"
        ]

        if not self.data.get("messages"):
            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "user",
                    "content": f"Below is the JSON API response for this sample, please start with a brief description of the experiment after a friendly welcome message of your choice. Please only reference the data in the JSON response, do not reference the data in the wiki or any other source. JSON data: {item_info}",
                },
            ]

        if self.data.get("prompt"):
            self.data["messages"].append(
                {
                    "role": "user",
                    "content": self.data["prompt"],
                }
            )
            self.data["prompt"] = None

        responses = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.data["messages"],
            temperature=0.9,
            max_tokens=1024,
            stop=["\n"],
        )
        # import random

        # responses = {
        #     "choices": [
        #         {"message": {"role": "system", "content": f"Hello {random.randint(0, 999)}"}}
        #     ]
        # }

        try:
            self.data["messages"].append(responses["choices"][0].message)
        except Exception:
            self.data["messages"].append(responses["choices"][0]["message"])

        p = figure(
            sizing_mode="scale_width",
            aspect_ratio=1.5,
            tools=["pan", "reset"],
        )
        p.axis.visible = False
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        offset = 0

        for ind, message in enumerate(self.data["messages"][2:]):
            try:
                role = message.role
                content = message.content
            except Exception:
                role = message["role"]
                content = message["content"]

            if role == "user":
                color = "blue"
                x = 1
                text_align = "right"
            else:
                color = "green"
                x = 0
                text_align = "left"
            y = -ind

            text = [line for line in textwrap.wrap(content, 65)]
            offset += len(text) - 1

            LOGGER.debug("%s %s", y - offset, text)
            bubble = Text(
                x=x,
                y=y - offset,
                text=["\n".join(text)],
                text_color=color,
                text_baseline="top",
                text_align=text_align,
            )
            p.add_glyph(bubble)

        p.x_range = Range1d(-0.2, 1.2)
        p.y_range = Range1d(-9, 1)

        self.data["bokeh_plot_data"] = bokeh.embed.json_item(p)
