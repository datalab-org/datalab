import json
from typing import Literal, Sequence

from pydantic import BaseModel

from pydatalab.models import ITEM_MODELS


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


def num_tokens_from_messages(
    messages: Sequence[dict | Message], model: str = "gpt-3.5-turbo-0613"
) -> int:
    """Count the number of tokens used in the current conversation
    with tiktoken.

    See https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    for more information.

    Returns:
        The number of tokens used in the conversation so far.

    """
    import tiktoken

    encoding = tiktoken.encoding_for_model(model)

    tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_name = -1  # if there's a name, the role is omitted

    num_tokens = 0
    for message in messages:
        if isinstance(message, Message):
            message = message.dict()
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def prepare_item_json_for_chat(item_id: str) -> str:
    """Retrieve and prepare the item data with the given ID for use in chat.

    This includes stripping out unnecessary or large fields,
    and converting the remaining data to a JSON string.

    Parameters:
        item_id: The ID of the item to prepare.

    Returns:
        A JSON string containing the prepared item data.

    """
    from pydatalab.routes.v0_1.items import get_item_data
    from pydatalab.utils import CustomJSONEncoder

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
    item_info["creators"] = [creator["display_name"] for creator in item_info.get("creators", [])]

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
                if "quantity" in constituent:
                    constituent[
                        "quantity"
                    ] = f"{constituent.get('quantity', 'unknown')} {constituent.get('unit', '')}"
                constituent.pop("unit", None)

    # Note manual replaces to help avoid escape sequences that take up extra tokens
    item_info_json_string = (
        json.dumps(item_info, cls=CustomJSONEncoder)
        .replace('"', "'")
        .replace(r"\'", "'")
        .replace(r"\n", " ")
    )

    return item_info_json_string


def prepare_collection_json_for_chat(collection_id: str) -> str:
    """Retrieve and prepare the collection data with the given ID for use in chat.

    This includes stripping out unnecessary or large fields,
    and converting the remaining data to a JSON string.

    Parameters:
        collection_id: The ID of the collection to prepare.

    Returns:
        A JSON string containing the prepared item data.

    """
    from pydatalab.routes.v0_1.collections import get_collection

    collection_data = get_collection(collection_id).json
    if collection_data["status"] != "success":
        raise RuntimeError(f"Attempt to get collection data for {collection_id} failed.")

    children = collection_data["child_items"]
    return (
        "[" + ",".join([prepare_item_json_for_chat(child["item_id"]) for child in children]) + "]"
    )
