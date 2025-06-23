# Load block types first to avoid circular dependency issues
from pydatalab.apps import BLOCK_TYPES, BLOCKS, load_block_plugins


def test_load_plugins():
    from datalab_app_plugin_insitu import InsituBlock

    plugins = load_block_plugins()

    assert plugins["insitu-nmr"] == InsituBlock
    assert isinstance(BLOCK_TYPES["insitu-nmr"], type)
    assert BLOCK_TYPES["insitu-nmr"] == InsituBlock
    assert InsituBlock in BLOCKS


def test_load_app_blocks():
    from pydatalab.apps import load_app_blocks
    from pydatalab.apps.echem import CycleBlock
    from pydatalab.apps.xrd import XRDBlock

    app_blocks = load_app_blocks()

    assert CycleBlock in app_blocks
    assert XRDBlock in app_blocks
