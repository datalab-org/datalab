from pydatalab.apps.chat import ChatBlock


def test_chatblock():
    chat = ChatBlock(item_id="test")
    chat.data["model"] = "langchain-debug"

    chat.start_conversation(item_data={"item_data": {"type": "samples", "item_id": "test"}})

    assert chat.data["messages"][0]["content"].startswith("You are whinchat (lowercase w)")
    assert chat.data["messages"][1]["content"].startswith("Here is the JSON data for")

    chat.render()
    assert chat.data["messages"][2]["role"] == "assistant"

    chat.data["prompt"] = "Hello there"
    chat.render()

    assert chat.data["messages"][-1] == {"role": "assistant", "content": "Hello there"}
    assert chat.data["messages"][-2] == {"role": "user", "content": "Hello there"}
    assert chat.data["messages"][0]["content"].startswith("You are whinchat (lowercase w)")
    assert chat.data["messages"][1]["content"].startswith("Here is the JSON data for")
    assert len(chat.data["messages"]) == 5

    chat.data["prompt"] = "Hello there again"
    chat.render()

    assert chat.data["messages"][-1] == {"role": "assistant", "content": "Hello there again"}
    assert chat.data["messages"][-2] == {"role": "user", "content": "Hello there again"}
    assert chat.data["messages"][0]["content"].startswith("You are whinchat (lowercase w)")
    assert chat.data["messages"][1]["content"].startswith("Here is the JSON data for")
    assert len(chat.data["messages"]) == 7
