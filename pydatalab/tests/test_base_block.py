from pydatalab.blocks import DataBlock


def test_base_block():
    block = DataBlock(item_id="test-id")
    test_event = {"event_name": "null_event", "kwargs": {"a": 1, "b": 2, "c": 1.2, "d": "string"}}
    block.process_events(test_event)
    assert block.data["kwargs"]["a"] == 1
    assert block.data["kwargs"]["b"] == 2
    assert block.data["kwargs"]["c"] == 1.2
    assert block.data["kwargs"]["d"] == "string"
