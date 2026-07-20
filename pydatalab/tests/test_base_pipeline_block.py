from pydatalab.pipeline_block.base import PipelineDataBlock
from pydatalab.pipeline_block.utils import generate_js_callback_single_float_parameter


def test_base_block():
    block = PipelineDataBlock(item_id="test-id")
    test_event = {"event_name": "null_event", "kwargs": {"a": 1, "b": 2, "c": 1.2, "d": "string"}}
    block.process_events(test_event)
    assert block.data["kwargs"]["a"] == 1
    assert block.data["kwargs"]["b"] == 2
    assert block.data["kwargs"]["c"] == 1.2
    assert block.data["kwargs"]["d"] == "string"


def test_callback():
    callback = generate_js_callback_single_float_parameter(
        "set_wavelength", "wavelength", block_id="test", throttled=False
    )
    assert (
        callback
        == """const block_event = new CustomEvent('block-event', {
    detail: {
        block_id: 'test',
        event_name: 'set_wavelength',
        wavelength: (cb_obj.value ?? cb_obj.text),
    }, bubbles: true
    });
document.dispatchEvent(block_event);"""
    )
