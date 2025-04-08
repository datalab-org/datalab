def test_load_plugins():
    from datalab_app_plugin_insitu import InsituBlock

    from pydatalab.blocks import BLOCK_TYPES, BLOCKS, load_block_plugins

    plugins = load_block_plugins()

    assert plugins["insitu-nmr"] == InsituBlock
    assert isinstance(BLOCK_TYPES["insitu-nmr"], type)
    assert BLOCK_TYPES["insitu-nmr"] == InsituBlock
    assert InsituBlock in BLOCKS
