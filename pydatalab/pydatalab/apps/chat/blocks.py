import os
from typing import Sequence

import openai

from pydatalab.blocks.blocks import DataBlock
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS

__all__ = "ChatBlock"


class ChatBlock(DataBlock):
    blocktype = "chat"
    description = "LLM Chat Block with contextual data (powered by GPT-3.5-turbo)"
    accepted_file_extensions: Sequence[str] = []
    defaults = {
        "system_prompt": """You are a virtual assistant that helps materials chemists manage their experimental data. You are deployed in the group of Professor Clare Grey in the Department of Chemistry at the University of Cambridge.

        You are embedded within the program datalab, where you have access to JSON that describes 'items'. These items may include experimental samples, starting materials, and devices (e.g. batteries made out of experimental samples and starting materials). Answer questions about the data as concisely as possible.

        Start the conversion with a friendly greeting introducing yourself.
        """,
    }
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def plot_functions(self):
        return (self.render,)

    def render(self):
        from pydatalab.routes.v0_1.graphs import get_graph_cy_format
        from pydatalab.routes.v0_1.items import get_item_data

        item_info = get_item_data(self.data["item_id"], load_blocks=False).json
        graph = get_graph_cy_format(self.data["item_id"])

        model = ITEM_MODELS[item_info["item_data"]["type"]](**item_info["item_data"])
        if model.blocks_obj:
            model.blocks_obj = {
                k: value for k, value in model.blocks_obj.items() if value["blocktype"] != "chat"
            }
        item_info = model.dict(exclude_none=True, exclude_unset=True, exclude_defaults=True)
        item_info["type"] = model.type
        # LOGGER.debug(item_info)

        # strip irrelevant or large fields
        for block in item_info.get("blocks_obj", {}).values():
            block.pop("bokeh_plot_data", None)

        top_level_keys_to_remove = [
            "display_order",
            "creator_ids",
            "refcode",
            "last_modified" "revision",
            "revisions",
            "immutable_id",
        ]
        for k in top_level_keys_to_remove:
            item_info.pop(k, None)

        for ind, f in enumerate(item_info.get("files", [])):
            item_info["files"][ind] = {k: v for k, v in f.items() if k in ["name", "extension"]}
        for ind, f in enumerate(item_info.get("relationships", [])):
            item_info["relationships"][ind] = {
                k: v for k, v in f.items() if k in ["item_id", "type", "relation"]
            }

        item_info = {k: value for k, value in item_info.items() if value}

        if not self.data.get("messages"):
            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "system",
                    "content": f"""The current item has item_id: {self.data['item_id']}. Here is a JSON that describes links between this sample and others: {graph}.

                    Here is the JSON data for the current item and others that are linked to it: {item_info}""",
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
            if self.data["messages"][-1].role not in ("user", "system"):
                return
        except AttributeError:
            if self.data["messages"][-1]["role"] not in ("user", "system"):
                return

        try:
            LOGGER.warning(
                f"submitting request to OpenAI API for completion with last message role \"{self.data['messages'][-1]['role']}\" (message = {self.data['messages'][-1:]})"
            )
            responses = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.data["messages"],
                temperature=0.9,
                max_tokens=1024,
            )
        except openai.InvalidRequestError as exc:
            LOGGER.debug("Received an InvalidRequestError from OpenAI API: %s", exc)
            return

        try:
            self.data["messages"].append(responses["choices"][0].message)
        except AttributeError:
            self.data["messages"].append(responses["choices"][0]["message"])
