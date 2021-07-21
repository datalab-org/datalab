from pydatalab.blocks.blocks import DataBlock, CommentBlock, ImageBlock, XRDBlock, CycleBlock


BLOCKS = (DataBlock, CommentBlock, ImageBlock, XRDBlock, CycleBlock)
BLOCK_KINDS = {block.blocktype: block for block in BLOCKS}
BLOCK_KINDS["test"] = DataBlock

__all__ = ("DataBlock", "CommentBlock", "ImageBlock", "XRDBlock", "CycleBlock", "BLOCK_KINDS", "BLOCKS")
