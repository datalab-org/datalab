import json
import warnings

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import Field, validator

from pydatalab.blocks.base import DataBlock
from pydatalab.models import ITEM_MODELS
from pydatalab.models.blocks import DataBlockResponse
from pydatalab.utils import CustomJSONEncoder

from .models import AVAILABLE_MODELS, ModelCard

__all__ = ("ChatBlock",)


class ChatBlockResponse(DataBlockResponse):
    messages: list[dict] = Field(default_factory=list)
    prompt: str | None
    model: str
    available_models: dict[str, ModelCard] | None = Field(
        datalab_exclude_from_db=True, datalab_exclude_from_load=True
    )
    token_count: int | None
    temperature: float

    @validator("available_models", pre=True, always=True)
    def set_available_models(cls, _):
        return AVAILABLE_MODELS


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

    > Jablonka *et al*, Digital Discovery, 2023,2, 1233-1250, DOI: [10.1039/d3dd00113j](https://doi.org/10.1039/d3dd00113j)

    """

    block_db_model = ChatBlockResponse

    blocktype = "chat"
    description = "Virtual LLM assistant block allows you to converse with your data."
    name = "Whinchat assistant"
    accepted_file_extensions = None

    __supports_collections = True

    defaults: dict = {
        "system_prompt": """You are whinchat (lowercase w), a virtual data managment assistant that helps materials chemists manage their experimental data and plan experiments. You are deployed in the group of Professor Clare Grey in the Department of Chemistry at the University of Cambridge.
You are embedded within the program datalab, where you have access to JSON describing an ‘item’, or a collection of items, with connections to other items. These items may include experimental samples, starting materials, and devices (e.g. battery cells made out of experimental samples and starting materials).
Answer questions in markdown. Specify the language for all markdown code blocks. You can make diagrams by writing a mermaid code block or an svg code block. When writing mermaid code, you must use quotations around each of the labels (e.g. A["label1"] --> B["label2"])
Be as concise as possible. When saying your name, type a bird emoji right after whinchat 🐦.
        """,
        "temperature": 0.2,
        "model": "gpt-4o",
        "available_models": AVAILABLE_MODELS,
    }

    @property
    def plot_functions(self):
        return (self.render,)

    def start_conversation(
        self, item_data: dict | None = None, collection_data: dict | None = None
    ):
        """Starts a new conversation with the system prompt, embedding
        the current item or collection data.

        """

        if (item_id := self.data.get("item_id")) is not None:
            info_json = self._prepare_item_json_for_chat(item_id, item_data=item_data)
        elif (collection_id := self.data.get("collection_id")) is not None:
            info_json = self._prepare_collection_json_for_chat(
                collection_id, collection_data=collection_data
            )
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

    def continue_conversation(self, prompt: str | None) -> None:
        """Continues the conversation based on the passed user prompt.

        Parameters:
            prompt: The textual response from the user.

        """
        if prompt and prompt.strip():
            self.data["messages"].append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )
            self.data["prompt"] = None

        try:
            if self.data["messages"][-1].role not in ("user", "system"):
                return
        except AttributeError:
            if self.data["messages"][-1]["role"] not in ("user", "system"):
                return

        if self.data.get("model") not in AVAILABLE_MODELS:
            bad_model = self.data.get("model")
            warnings.warn(
                f"Chatblock received an unknown or deprecated model: {bad_model}. Reverting to default model {self.defaults['model']}."
            )
            self.data["model"] = self.defaults["model"]

        try:
            model_name = self.data["model"]

            model_cls = AVAILABLE_MODELS[model_name]

            if model_cls.chat_client is None:
                raise RuntimeError(
                    f"The model {model_name} is not available. Please choose a different model."
                )

            chat_client = model_cls.chat_client(model=model_cls.name)

            # Convert your messages to the required format
            langchain_messages = []
            for message in self.data["messages"]:
                if message["role"] == "user":
                    langchain_messages.append(HumanMessage(content=message["content"]))
                elif message["role"] == "system":
                    langchain_messages.append(SystemMessage(content=message["content"]))
                else:
                    langchain_messages.append(AIMessage(content=message["content"]))

            if model_cls.name == "langchain-debug":
                token_count = sum(len(m["content"]) for m in self.data["messages"])
            else:
                token_count = chat_client.get_num_tokens_from_messages(langchain_messages)

            self.data["token_count"] = token_count

            if token_count >= model_cls.context_window:
                raise RuntimeError(
                    f"""This conversation has reached its maximum context size and the chatbot won't be able to respond further
({token_count} tokens, max: {model_cls.context_window}).
Please make a new chat block to start fresh, or use a model with a larger context window."""
                )

            # Call the chat client with the invoke method
            response = chat_client.invoke(langchain_messages)

            langchain_messages.append(response)

            # Now recalculate the token count after model output
            self.data["messages"].append({"role": "assistant", "content": response.content})
            if model_cls.name == "langchain-debug":
                token_count = sum(len(m["content"]) for m in self.data["messages"])
            else:
                token_count = chat_client.get_num_tokens_from_messages(langchain_messages)
            self.data["token_count"] = token_count

        except Exception as exc:
            raise RuntimeError(
                f"Received an error from the API: {exc}.\n\n Consider choosing a different model and reloading the block."
            )

    def render(self):
        if not self.data.get("messages"):
            self.start_conversation()

        self.continue_conversation(self.data.get("prompt"))

    def _prepare_item_json_for_chat(self, item_id: str, item_data: dict | None = None):
        from pydatalab.routes.v0_1.items import get_item_data

        if item_data is None:
            item_data = get_item_data(item_id).json

            if item_data["status"] != "success":
                raise RuntimeError(f"Attempt to get item data for {item_id=} failed.")

        item_model = ITEM_MODELS[item_data["item_data"]["type"]](**item_data["item_data"])
        if item_model.blocks_obj:
            item_model.blocks_obj = {
                k: block for k, block in item_model.blocks_obj.items() if block.blocktype != "chat"
            }
        item_data = item_model.dict(exclude_none=True, exclude_unset=True)
        item_data["type"] = item_model.type

        # strip irrelevant or large fields
        item_filenames = {
            str(file["immutable_id"]): file["name"] for file in item_data.get("files", [])
        }

        big_data_keys = ["bokeh_plot_data", "b64_encoded_image", "computed"]
        for block in item_data.get("blocks_obj", {}).values():
            block_fields_to_remove = ["item_id", "block_id", "collection_id"] + big_data_keys
            [block.pop(field, None) for field in block_fields_to_remove]

            # nmr block fields to remove (need a more general way to do this)
            NMR_fields_to_remove = [
                "acquisition_parameters",
                "carrier_offset_Hz",
                "nscans",
                "processed_data_shape",
                "processing_parameters",
                "pulse_program",
                "selected_process",
            ]
            if "metadata" in block:
                [block["metadata"].pop(field, None) for field in NMR_fields_to_remove]

            # replace file_id with the actual filename
            file_id = block.pop("file_id", None)
            if file_id:
                block["file"] = item_filenames.get(file_id)

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
            item_data.pop(k, None)

        for ind, f in enumerate(item_data.get("relationships", [])):
            item_data["relationships"][ind] = {
                k: v for k, v in f.items() if k in ["item_id", "type", "relation"]
            }
        item_data["files"] = [file["name"] for file in item_data.get("files", [])]
        item_data["creators"] = [
            creator["display_name"] for creator in item_data.get("creators", [])
        ]

        # move blocks from blocks_obj to a simpler list to further cut down tokens,
        # especially in alphanumeric block_id fields
        item_data["blocks"] = [block for block in item_data.pop("blocks_obj", {}).values()]

        item_data = {k: value for k, value in item_data.items() if value}

        for key in [
            "synthesis_constituents",
            "positive_electrode",
            "negative_electrode",
            "electrolyte",
        ]:
            if key in item_data:
                for constituent in item_data[key]:
                    if "quantity" in constituent:
                        constituent["quantity"] = (
                            f"{constituent.get('quantity', 'unknown')} {constituent.get('unit', '')}"
                        )
                    constituent.pop("unit", None)

        # Note manual replaces to help avoid escape sequences that take up extra tokens
        item_info_json = (
            json.dumps(item_data, cls=CustomJSONEncoder)
            .replace('"', "'")
            .replace(r"\'", "'")
            .replace(r"\n", " ")
        )

        return item_info_json

    def _prepare_collection_json_for_chat(
        self, collection_id: str, collection_data: dict | None = None
    ):
        from pydatalab.routes.v0_1.collections import get_collection

        if not collection_data:
            collection_data = get_collection(collection_id).json

            if collection_data["status"] != "success":
                raise RuntimeError(f"Attempt to get collection data for {collection_id} failed.")

        children = collection_data["child_items"]
        return (
            "["
            + ",".join([self._prepare_item_json_for_chat(child["item_id"]) for child in children])
            + "]"
        )
