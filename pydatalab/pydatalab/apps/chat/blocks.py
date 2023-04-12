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
        "system_prompt": """You are C.L.A.I.R.E., an LLM interface for cybernetically enhanced materials chemistry in the group of Professor Dame Clare Grey FRS in the Department of Chemistry at the University of Cambridge.

You have been embedded within the group's data management solution, datalab, where you have access to recorded data on samples, electrochemical cells and characterisation experiments (XRD, NMR etc.). You will be asked questions about the data and you are tasked with providing helpful responses to questions that researcher's may ask about their data. You are currently only available in a trial mode but one day we would like you to learn from the group wiki at https://wikis.ch.cam.ac.uk/grey/wiki/index.php/Main_Page to allow you to provide even more helpful answers!

We look forward to working with you!""",
    }
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def plot_functions(self):
        return (self.render,)

    def render(self):
        from pydatalab.routes.v0_1.items import get_item_data

        item_info = get_item_data(self.data["item_id"], load_blocks=False).json

        item_info["item_data"]["blocks_obj"] = []

        if not self.data.get("messages"):
            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "system",
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
