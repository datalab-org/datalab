import os
from typing import Sequence

import openai

from pydatalab.blocks.blocks import DataBlock

__all__ = "ChatBlock"


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
        from pydatalab.routes.v0_1.items import get_item_data

        item_info = get_item_data(self.data["item_id"], load_blocks=False).json
        graph = get_graph_cy_format(self.data["item_id"])

        item_info["item_data"]["blocks_obj"] = []

        if not self.data.get("messages"):
            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "system",
                    "content": f"""The current item has item_id: {self.data['item_id']}. Here is a JSON that describes links between this sample and others: {graph}.

                    Here is a json file that describes the current item and others that are linked to it: {item_info}""",
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

        responses = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.data["messages"],
            temperature=0.9,
            max_tokens=1024,
            stop=["\n"],
        )

        try:
            self.data["messages"].append(responses["choices"][0].message)
        except Exception:
            self.data["messages"].append(responses["choices"][0]["message"])
