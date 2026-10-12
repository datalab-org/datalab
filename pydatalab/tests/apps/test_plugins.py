# Load block types first to avoid circular dependency issues


def test_load_app_blocks():
    from pydatalab.apps import load_app_blocks
    from pydatalab.apps.echem import CycleBlock
    from pydatalab.apps.xrd import XRDBlock

    app_blocks = load_app_blocks()

    assert CycleBlock in app_blocks
    assert XRDBlock in app_blocks
