import json
import os
from typing import Sequence

import openai

from pydatalab.blocks.blocks import DataBlock
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS
from pydatalab.utils import CustomJSONEncoder

__all__ = "ChatBlock"


class ChatBlock(DataBlock):
    blocktype = "chat"
    description = "LLM Chat Block with contextual data (powered by GPT-3.5-turbo)"
    accepted_file_extensions: Sequence[str] = []
    defaults = {
        "system_prompt": """You are a virtual assistant that helps materials chemists manage their experimental data and plan experiments. You are deployed in the group of Professor Clare Grey in the Department of Chemistry at the University of Cambridge.
You are embedded within the program datalab, where you have access to JSON describing an ‘item’ with connections to other items. These items may include experimental samples, starting materials, and devices (e.g. battery cells made out of experimental samples and starting materials).
Answer questions in markdown. Specify the language for all markdown code blocks. You can make diagrams by writing a mermaid code block or an svg code block.
Be as concise as possible. Start the conversion with a friendly greeting introducing yourself.
        """,
    }
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def plot_functions(self):
        return (self.render,)

    def render(self):
        from pydatalab.routes.v0_1.items import get_item_data

        item_info = get_item_data(self.data["item_id"], load_blocks=False).json

        model = ITEM_MODELS[item_info["item_data"]["type"]](**item_info["item_data"])
        if model.blocks_obj:
            model.blocks_obj = {
                k: value for k, value in model.blocks_obj.items() if value["blocktype"] != "chat"
            }
        item_info = model.dict(exclude_none=True, exclude_unset=True)
        item_info["type"] = model.type
        # LOGGER.debug(item_info)

        # strip irrelevant or large fields
        for block in item_info.get("blocks_obj", {}).values():
            block.pop("bokeh_plot_data", None)

        top_level_keys_to_remove = [
            "display_order",
            "creator_ids",
            "refcode",
            "last_modified",
            "revision",
            "revisions",
            "immutable_id",
            "file_ObjectIds",
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

        for key in [
            "synthesis_constituents",
            "positive_electrode",
            "negative_electrode",
            "electrolyte",
        ]:
            if key in item_info:
                for constituent in item_info[key]:
                    LOGGER.debug("iterating through constituents:")
                    LOGGER.debug(constituent)
                    if "quantity" in constituent:
                        constituent[
                            "quantity"
                        ] = f"{constituent.get('quantity', 'unknown')} {constituent.get('unit', '')}"
                    constituent.pop("unit", None)

        # Note manual replaces to help avoid escape sequences that take up extra tokens
        item_info_json = (
            json.dumps(item_info, cls=CustomJSONEncoder)
            .replace('"', "'")
            .replace(r"\'", "'")
            .replace(r"\n", " ")
        )

        if not self.data.get("messages"):
            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "user",
                    "content": f"""Here is the JSON data for the current item: {item_info_json}""",
                },
            ]
        # for debugging:
        # with open("test_item_info.json", "w") as f:
        #     f.write(self.data["messages"][-1]["content"])

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
                temperature=0.2,
                max_tokens=1024,
            )
        except openai.InvalidRequestError as exc:
            LOGGER.debug("Received an InvalidRequestError from OpenAI API: %s", exc)
            return

        try:
            self.data["messages"].append(responses["choices"][0].message)
        except AttributeError:
            self.data["messages"].append(responses["choices"][0]["message"])
