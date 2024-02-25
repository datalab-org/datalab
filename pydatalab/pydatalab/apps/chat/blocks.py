import os
from typing import Callable, Sequence

import openai
from pydantic import Field

from pydatalab.blocks.base import BlockDataModel, BlockMetadata, DataBlock
from pydatalab.logger import LOGGER

from .utils import (
    Message,
    num_tokens_from_messages,
    prepare_collection_json_for_chat,
    prepare_item_json_for_chat,
)

__all__ = ("ChatBlock",)


class ChatBlockMetadata(BlockMetadata):
    temperature: float = Field(
        0.2,
        title="Temperature",
        description="The randomness of the chatbot's responses. A higher temperature will make the chatbot more creative, but also more likely to make mistakes.",
    )
    system_prompt: str = Field(
        """You are whinchat (lowercase w), a virtual data managment assistant that helps materials chemists manage their experimental data and plan experiments.
You are deployed in the group of Professor Clare Grey in the Department of Chemistry at the University of Cambridge.
You are embedded within the program datalab, where you have access to JSON describing an ‘item’, or a collection of items, with connections to other items.
These items may include experimental samples, starting materials, and devices (e.g. battery cells made out of experimental samples and starting materials).
Answer questions in markdown. Specify the language for all markdown code blocks. You can make diagrams by writing a mermaid code block or an svg code block.
When writing mermaid code, you must use quotations around each of the labels (e.g. A["label1"] --> B["label2"])
Be as concise as possible.
When saying your name, type a bird emoji right after whinchat 🐦."""
    )
    user_prompt: str = Field(
        """Here is the JSON data for the current item(s): {info_json}.
Start with a friendly introduction and give me a one sentence summary of what this is (not detailed, no information about specific masses)."""
    )


class ChatBlockDataModel(BlockDataModel):
    metadata: ChatBlockMetadata = ChatBlockMetadata()
    messages: list[Message] = []
    prompt: str | None = None
    token_count: int = 0
    max_context_size: int = 4097
    model_name: str = "gpt-3.5-turbo-0613"


class ChatBlock(DataBlock):
    blocktype = "chat"
    title = "Virtual assistant"
    accepted_file_extensions: Sequence[str] = []
    data_model = ChatBlockDataModel

    _supports_collections = True

    openai.api_key = os.environ.get("OPENAI_API_KEY")

    def to_db(self):
        """returns a dictionary with the data for this
        block, ready to be input into mongodb"""
        self.render()
        return super().to_db()

    @property
    def plot_functions(self) -> Sequence[Callable[[], None]]:
        return (self.render,)

    def render(self) -> None:
        """Render the chat block based on the state.

        If a conversation is ongoing, check for a new message and request a response to it.
        If the conversation has ended (i.e., the last message was from the assistant), do nothing.
        If no conversation is ongoing, start a new conversation with the system prompt and
        the current item data.

        """

        if not self.data.messages:
            # Kick off the conversation with item/collection data and the system prompt
            if (item_id := self.data.item_id) is not None:
                info_json = prepare_item_json_for_chat(item_id)
            elif (collection_id := self.data.collection_id) is not None:
                info_json = prepare_collection_json_for_chat(collection_id)
            else:
                raise RuntimeError("No item or collection id provided.")

            self.data.messages = [
                Message(role="system", content=self.data.metadata.system_prompt),
                Message(
                    role="user", content=self.data.metadata.user_prompt.format(info_json=info_json)
                ),
            ]

        # If the user has provided a message via the UI
        if self.data.prompt:
            self.data.messages.append(Message(role="user", content=self.data.prompt))
            self.data.prompt = None

        token_count = num_tokens_from_messages(self.data.messages, model=self.data.model_name)
        self.data.token_count = token_count

        if token_count >= self.data.max_context_size:
            self.data.errors.append(
                f"This conversation has reached its maximum context size and the chatbot won't be able to respond further ({token_count=}, {self.data.max_context_size=}). "
                "Please make a new chat block to start fresh."
            )
            return

        # If the last message was from the assistant, do nothing and return
        if self.data.messages[-1].role not in ("user", "system"):
            return

        # Otherwise, request the response from OpenAI
        try:
            LOGGER.debug(
                "Submitting request to OpenAI API for completion with last message %s, temperature = %s)",
                self.data.messages[-1],
                self.data.metadata.temperature,
            )
            responses = openai.ChatCompletion.create(
                model=self.data.model_name,
                messages=[m.dict() for m in self.data.messages],
                temperature=self.data.metadata.temperature,
                max_tokens=min(
                    1024, self.data.max_context_size - token_count - 1
                ),  # if less than 1024 tokens are left in the token, then indicate this
            )
            self.data.errors = None
        except openai.OpenAIError as exc:
            error = f"Received an error from the OpenAI API: {exc}."
            LOGGER.debug(error)
            self.data.errors = [error]
            return

        try:
            self.data.messages.append(responses["choices"][0].message)
        except AttributeError:
            self.data.messages.append(responses["choices"][0]["message"])

        self.data.token_count = num_tokens_from_messages(self.data.messages)
