import json
import os
from typing import Sequence

import openai

from pydatalab.apps.chat.item_models_for_chat import Cell, Sample
from pydatalab.blocks.blocks import DataBlock
from pydatalab.mongo import flask_mongo
from pydatalab.utils import CustomJSONEncoder

__all__ = "ChatBlock"

ITEM_MODELS = {
    "samples": Sample,
    "cells": Cell,
}


def get_item_data_for_chat(item_id):
    cursor = flask_mongo.db.items.aggregate(
        [
            {"$match": {"item_id": item_id}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "creator_ids",
                    "foreignField": "_id",
                    "as": "creators",
                }
            },
            {
                "$lookup": {
                    "from": "files",
                    "localField": "file_ObjectIds",
                    "foreignField": "_id",
                    "as": "files",
                }
            },
        ]
    )
    doc = list(cursor)[0]

    ItemModel = ITEM_MODELS[doc["type"]]

    item = ItemModel(**doc)

    item_dict = item.dict(exclude_none=True)

    item_dict["blocks"] = [value for value in item_dict["blocks_obj"].values()]
    del item_dict["blocks_obj"]

    output = json.dumps(item_dict, cls=CustomJSONEncoder)
    return output


class ChatBlock(DataBlock):
    blocktype = "chat"
    description = "LLM Chat Block with contextual data (powered by GPT-3.5-turbo)"
    accepted_file_extensions: Sequence[str] = []
    defaults = {
        "system_prompt": """You are a virtual assistant that helps materials chemists manage their experimental data. You are deployed in the group of Professor Clare Grey in the Department of Chemistry at the University of Cambridge.

        You are embedded within the program datalab, where you have access to json that describes 'items'. These items may include experimental samples, starting materials, and devices (e.g. batteries made out of experimental samples and starting materials). Answer questions about the data as concisely as possible.

        Start the conversion with a friendly greeting introducing yourself.
        """,
    }
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def plot_functions(self):
        return (self.render,)

    def render(self):
        from pydatalab.routes.v0_1.graphs import get_graph_cy_format

        # item_info = get_item_data(self.data["item_id"], load_blocks=False).json
        graph = get_graph_cy_format()[0].json

        item_infos = [
            get_item_data_for_chat(node["data"]["id"])
            for node in graph["nodes"]
            if node["data"]["type"] != "starting_materials"
        ]

        if not self.data.get("messages"):
            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "user",
                    "content": f"""The current item has item_id: {self.data['item_id']}. Here is a json file that describes the current item and others that are linked to it: {item_infos}""",
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

        try:
            if self.data["messages"][-1].role == "assistant":
                return
        except Exception:
            if self.data["messages"][-1]["role"] == "assistant":
                return

        print(item_infos)
        responses = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.data["messages"],
            temperature=0.9,
            max_tokens=1024,
            # stop=["\n"],
            n=1,
        )

        try:
            self.data["messages"].append(responses["choices"][0].message)
        except Exception:
            self.data["messages"].append(responses["choices"][0]["message"])
