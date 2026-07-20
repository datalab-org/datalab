import random


def generate_js_callback_single_float_parameter(
    event_name: str, parameter: str, block_id: str, throttled: bool = False
) -> str:
    """Generates a Bokeh JS callback that can be attached
    to a widget and used to trigger datalab block events with
    a single named parameter.

    Parameters:
        event_name: The name of the block method to call.
        parameter: The name of the parameter to update.
        block_id: The ID of the block to target for the event.
        throttled: Whether to bind to the widget's `value` or `value_throttled`.

    """

    event_target: str = (
        "(cb_obj.value_throttled ?? cb_obj.value ?? cb_obj.text)"
        if throttled
        else "(cb_obj.value ?? cb_obj.text)"
    )

    code = (
        r"""
const block_event = new CustomEvent('block-event', {
    detail: {
        block_id: '$block_id',
        event_name: '$event_name',
        $parameter: $event_target,
    }, bubbles: true
});
document.dispatchEvent(block_event);
""".replace("$event_name", event_name)
        .replace("$parameter", parameter)
        .replace("$event_target", event_target)
        .replace("$block_id", block_id)
    )
    return code.strip()


def generate_random_id():
    """This function generates a random 15-length string for use as an id for a datablock. It
    should be sufficiently random that there is a negligible risk of ever generating
    the same id twice, so this is a unique id that can be used as a unique database refrence
    and also can be used as id in the DOM. Note: uuid.uuid4() would do this too, but I think
    the generated ids are too long and ugly.

    The ids here are HTML id friendly, using lowercase letters and numbers. The first character
    is always a letter.
    """
    randlist = [random.choice("abcdefghijklmnopqrstuvwxyz")] + random.choices(  # noqa: S311
        "abcdefghijklmnopqrstuvwxyz0123456789", k=14
    )
    return "".join(randlist)
