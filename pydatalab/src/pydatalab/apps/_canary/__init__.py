import time

from pydatalab.blocks.base import DataBlock

raise ImportError("This canary block is only used for internal testing of dynamic block loading.")


class CanaryBlock(DataBlock): ...


class AsyncCanaryBlock(DataBlock):
    blocktype = "canary_async"
    description = "Async canary block for testing asynchronous processing"
    accepted_file_extensions = []
    prefers_async = True

    def to_web(self):
        time.sleep(2)
        web_dict = super().to_web()
        web_dict["processing_time"] = "2 seconds"
        web_dict["test_result"] = "async processing complete"
        return web_dict
