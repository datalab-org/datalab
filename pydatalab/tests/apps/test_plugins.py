# Load block types first to avoid circular dependency issues
from pydatalab.blocks import BLOCK_TYPES, BLOCKS, load_block_plugins


def test_load_plugins():
    from datalab_app_plugin_insitu import InsituBlock

    plugins = load_block_plugins()

    assert plugins["insitu-nmr"] == InsituBlock
    assert isinstance(BLOCK_TYPES["insitu-nmr"], type)
    assert BLOCK_TYPES["insitu-nmr"] == InsituBlock
    assert InsituBlock in BLOCKS
