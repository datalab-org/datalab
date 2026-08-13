from collections.abc import Callable
from typing import Any

from pydatalab.pipeline_block.block_stages.abstract_stage import BlockStage, Stage


class EventStage(BlockStage):
    """Stages for events"""

    function: "Callable[..., None]"
    """The event stage function, takes the data dictionary and any amount of **args"""

    def validate_input(self, function_input: Any) -> bool:
        return True

    def __init__(self, function: "Callable[..., None]"):
        """
        :param function: The event stage function, takes the data dictionary and any amount of **args
        """
        super().__init__(function, stage=Stage.EVENT)

    def perform(self, function_input: dict, *args, **kwargs) -> None:
        kwargs.pop("block_id", None)
        self.function(function_input, **kwargs)
