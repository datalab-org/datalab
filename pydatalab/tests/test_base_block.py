from pydatalab.blocks.base import DataBlock, generate_js_callback_single_float_parameter


def test_base_block():
    block = DataBlock(item_id="test-id")
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


def test_heavy_and_server_authoritative_keys_ignored_from_web():
    """Test that large plot data and server-authoritative fields posted by a client are neither
    loaded from the request nor written to the database.

    The webapp strips these keys from `blocks_obj` before saving an item; this pins the
    server-side behaviour that makes that safe, i.e. that sending them or not produces
    an identical database document.
    """
    import copy

    from pydatalab.apps import BLOCK_TYPES

    block_type = BLOCK_TYPES["comment"]
    excluded = ("bokeh_plot_data", "b64_encoded_image", "computed", "processed", "metadata")

    web_data = {
        "block_id": "block-1",
        "blocktype": "comment",
        "item_id": "test-item",
        "title": "A comment",
        "freeform_comment": "hello",
        "bokeh_plot_data": {"large": "x" * 1000},
        "b64_encoded_image": {"1": "y" * 1000},
        "computed": {"peaks": [1, 2, 3]},
        "metadata": {"acquired": "from the web"},
    }
    stored_data = {
        "block_id": "block-1",
        "blocktype": "comment",
        "item_id": "test-item",
        "computed": {"peaks": [9, 9]},
        "metadata": {"acquired": "from the database"},
    }

    with_heavy_keys = block_type.from_web(
        copy.deepcopy(web_data), stored_data=copy.deepcopy(stored_data)
    ).to_db()

    stripped = {k: v for k, v in web_data.items() if k not in excluded}
    without_heavy_keys = block_type.from_web(
        copy.deepcopy(stripped), stored_data=copy.deepcopy(stored_data)
    ).to_db()

    assert with_heavy_keys == without_heavy_keys

    # Plot data is never stored, and the stored values of the server-authoritative
    # fields win over whatever the client sent.
    assert "bokeh_plot_data" not in with_heavy_keys
    assert "b64_encoded_image" not in with_heavy_keys
    assert with_heavy_keys["computed"] == {"peaks": [9, 9]}
    assert with_heavy_keys["metadata"] == {"acquired": "from the database"}

    # The same holds on the first save of a block, when there is no stored state.
    assert (
        block_type.from_web(copy.deepcopy(web_data), stored_data=None).to_db()
        == block_type.from_web(copy.deepcopy(stripped), stored_data=None).to_db()
    )
