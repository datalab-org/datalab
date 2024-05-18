import json
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from pydatalab.blocks.base import DataBlock
from pydatalab.logger import LOGGER
from pydatalab.models import ITEM_MODELS
from pydatalab.utils import CustomJSONEncoder

__all__ = "ChatBlock"


class ChatBlock(DataBlock):
    """This block uses API calls to external LLMs via Langchain to provide a conversational
    interface to a user's data.

    Implemented models include:
    - the GPT series of models from OpenAI
    - Claude from Anthropic

    Each needs the server to be configured with the corresponding API keys:
    - `OPENAI_API_KEY`,
    - `ANTHROPIC_API_KEY`.

    A discussion of this block can be found in:

        Jablonka *et al*, Digital Discovery, 2023,2, 1233-1250, DOI: 10.1039/d3dd00113j

    """

    blocktype = "chat"
    description = "Virtual LLM assistant block allows you to converse with your data."
    name = "💬 Chat with Whinchat"
    accepted_file_extensions = None
    chat_client: BaseChatModel | None = None

    __supports_collections = True

    defaults = {
        "system_prompt": """You are whinchat (lowercase w), a virtual data managment assistant that helps materials chemists manage their experimental data and plan experiments. You are deployed in the group of Professor Clare Grey in the Department of Chemistry at the University of Cambridge.
You are embedded within the program datalab, where you have access to JSON describing an ‘item’, or a collection of items, with connections to other items. These items may include experimental samples, starting materials, and devices (e.g. battery cells made out of experimental samples and starting materials).
Answer questions in markdown. Specify the language for all markdown code blocks. You can make diagrams by writing a mermaid code block or an svg code block. When writing mermaid code, you must use quotations around each of the labels (e.g. A["label1"] --> B["label2"])
Be as concise as possible. When saying your name, type a bird emoji right after whinchat 🐦.
        """,
        "temperature": 0.2,
        "error_message": None,
        "model": "gpt-3.5-turbo-0613",
        "available_models": {
            "claude-3-haiku-20240307": {
                "name": "claude-3-haiku-20240307",
                "context_window": 200000,
                "input_cost_usd_per_MTok": 0.25,
                "output_cost_usd_per_MTok": 1.25,
            },
            "claude-3-opus-20240229": {
                "name": "claude-3-opus-20240229",
                "context_window": 200000,
                "input_cost_usd_per_MTok": 15.00,
                "output_cost_usd_per_MTok": 75.00,
            },
            "claude-3-sonnet-20240229": {
                "name": "claude-3-sonnet-20240229",
                "context_window": 200000,
                "input_cost_usd_per_MTok": 3.00,
                "output_cost_usd_per_MTok": 15.00,
            },
            "gpt-3.5-turbo-0613": {
                "name": "gpt-3.5-turbo-0613",
                "context_window": 4096,
                "input_cost_usd_per_MTok": 1.50,
                "output_cost_usd_per_MTok": 2.00,
            },
            "gpt-4": {
                "name": "gpt-4",
                "context_window": 8192,
                "input_cost_usd_per_MTok": 30.00,
                "output_cost_usd_per_MTok": 60.00,
            },
            "gpt-4-0125-preview": {
                "name": "gpt-4-0125-preview",
                "context_window": 128000,
                "input_cost_usd_per_MTok": 10.00,
                "output_cost_usd_per_MTok": 30.00,
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_db(self):
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""
        self.render()
        return super().to_db()

    @property
    def plot_functions(self):
        return (self.render,)

    def render(self):
        if not self.data.get("messages"):
            if (item_id := self.data.get("item_id")) is not None:
                info_json = self._prepare_item_json_for_chat(item_id)
            elif (collection_id := self.data.get("collection_id")) is not None:
                info_json = self._prepare_collection_json_for_chat(collection_id)
            else:
                raise RuntimeError("No item or collection id provided")

            self.data["messages"] = [
                {
                    "role": "system",
                    "content": self.defaults["system_prompt"],
                },
                {
                    "role": "user",
                    "content": f"""Here is the JSON data for the current item(s): {info_json}.
Start with a friendly introduction and give me a one sentence summary of what this is (not detailed, no information about specific masses). """,
                },
            ]

        if self.data.get("prompt") and self.data.get("prompt").strip():
            self.data["messages"].append(
                {
                    "role": "user",
                    "content": self.data["prompt"],
                }
            )
            self.data["prompt"] = None
        else:
            LOGGER.debug(
                "Chat block: no prompt was provided (or prompt was entirely whitespace), so no inference will be performed"
            )

        try:
            if self.data["messages"][-1].role not in ("user", "system"):
                return
        except AttributeError:
            if self.data["messages"][-1]["role"] not in ("user", "system"):
                return

        if self.data.get("model") not in self.data.get("available_models", {}):
            self.data["error_message"] = (
                f"Chatblock received an unknown model: {self.data.get('model')}"
            )
            return

        try:
            model_name = self.data["model"]

            model_dict = self.data["available_models"][model_name]
            LOGGER.warning(f"Initializing chatblock with model: {model_name}")

            if model_name.startswith("claude"):
                self.chat_client = ChatAnthropic(
                    anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
                    model=model_name,
                )
            elif model_name.startswith("gpt"):
                self.chat_client = ChatOpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    model=model_name,
                )

            LOGGER.debug(
                f"submitting request to API for completion with last message role \"{self.data['messages'][-1]['role']}\" (message = {self.data['messages'][-1:]}). Temperature = {self.data['temperature']} (type {type(self.data['temperature'])})"
            )
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

            # Convert your messages to the required format
            langchain_messages = []
            for message in self.data["messages"]:
                if message["role"] == "user":
                    langchain_messages.append(HumanMessage(content=message["content"]))
                elif message["role"] == "system":
                    langchain_messages.append(SystemMessage(content=message["content"]))
                else:
                    langchain_messages.append(AIMessage(content=message["content"]))

            token_count = self.chat_client.get_num_tokens_from_messages(langchain_messages)

            self.data["token_count"] = token_count

            if token_count >= model_dict["context_window"]:
                self.data["error_message"] = (
                    f"""This conversation has reached its maximum context size and the chatbot won't be able to respond further ({token_count} tokens, max: {model_dict['context_window']}). Please make a new chat block to start fresh, or use a model with a larger context window"""
                )
                return

            # Call the chat client with the invoke method
            response = self.chat_client.invoke(langchain_messages)

            langchain_messages.append(response)

            token_count = self.chat_client.get_num_tokens_from_messages(langchain_messages)

            self.data["token_count"] = token_count
            self.data["messages"].append({"role": "assistant", "content": response.content})
            self.data["error_message"] = None

        except Exception as exc:
            LOGGER.debug("Received an error from API: %s", exc)
            self.data["error_message"] = (
                f"Received an error from the API: {exc}.\n\n Consider choosing a different model and reloading the block."
            )
            return

    def _prepare_item_json_for_chat(self, item_id: str):
        from pydatalab.routes.v0_1.items import get_item_data

        item_info = get_item_data(item_id, load_blocks=False).json

        model = ITEM_MODELS[item_info["item_data"]["type"]](**item_info["item_data"])
        if model.blocks_obj:
            model.blocks_obj = {
                k: value for k, value in model.blocks_obj.items() if value["blocktype"] != "chat"
            }
        item_info = model.dict(exclude_none=True, exclude_unset=True)
        item_info["type"] = model.type

        # strip irrelevant or large fields
        item_filenames = {
            str(file["immutable_id"]): file["name"] for file in item_info.get("files", [])
        }
        for block in item_info.get("blocks_obj", {}).values():
            block.pop("bokeh_plot_data", None)

            block_fields_to_remove = ["item_id", "block_id"]
            [block.pop(field, None) for field in block_fields_to_remove]

            # nmr block fields to remove (need a more general way to do this)
            NMR_fields_to_remove = [
                "acquisition_parameters",
                "carrier_offset_Hz",
                "nscans",
                "processed_data",
                "processed_data_shape",
                "processing_parameters",
                "pulse_program",
                "selected_process",
            ]
            [block.pop(field, None) for field in NMR_fields_to_remove]

            # replace file_id with the actual filename
            file_id = block.pop("file_id", None)
            if file_id:
                block["file"] = item_filenames.get(file_id, None)

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

        for ind, f in enumerate(item_info.get("relationships", [])):
            item_info["relationships"][ind] = {
                k: v for k, v in f.items() if k in ["item_id", "type", "relation"]
            }
        item_info["files"] = [file["name"] for file in item_info.get("files", [])]
        item_info["creators"] = [
            creator["display_name"] for creator in item_info.get("creators", [])
        ]

        # move blocks from blocks_obj to a simpler list to further cut down tokens,
        # especially in alphanumeric block_id fields
        item_info["blocks"] = [block for block in item_info.pop("blocks_obj", {}).values()]

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
                        constituent["quantity"] = (
                            f"{constituent.get('quantity', 'unknown')} {constituent.get('unit', '')}"
                        )
                    constituent.pop("unit", None)

        # Note manual replaces to help avoid escape sequences that take up extra tokens
        item_info_json = (
            json.dumps(item_info, cls=CustomJSONEncoder)
            .replace('"', "'")
            .replace(r"\'", "'")
            .replace(r"\n", " ")
        )

        return item_info_json

    def _prepare_collection_json_for_chat(self, collection_id: str):
        from pydatalab.routes.v0_1.collections import get_collection

        collection_data = get_collection(collection_id).json
        if collection_data["status"] != "success":
            raise RuntimeError(f"Attempt to get collection data for {collection_id} failed.")

        children = collection_data["child_items"]
        return (
            "["
            + ",".join([self._prepare_item_json_for_chat(child["item_id"]) for child in children])
            + "]"
        )
