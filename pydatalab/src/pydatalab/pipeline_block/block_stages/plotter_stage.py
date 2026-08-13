from collections.abc import Callable
from typing import Any

import pandas as pd

from pydatalab.logger import LOGGER
from pydatalab.pipeline_block.block_stages.abstract_stage import BlockStage, Stage


class PlotterStage(BlockStage):
    function: "Callable[..., Any]"
    """The plotter stage"""

    def validate_input(self, function_input: Any) -> bool:
        # TODO validate input
        return True

    def __init__(
        self,
        function: "Callable[..., Any]",
        list_df_input: bool = False,
        accepted_data: list[str] | None = None,
    ):
        super().__init__(
            function, list_df_input=list_df_input, accepted_data=accepted_data, stage=Stage.PLOTTER
        )

    def perform(self, function_input: "pd.DataFrame|list[pd.DataFrame]", *args, **kwargs) -> Any:
        if function_input is None:
            return None
        if type(function_input) is list and not self.list_df_input:
            LOGGER.debug("This plotter does not support lists.")
            raise ValueError("This plotter does not accept lists.")
        if not self.check_args(list(kwargs.keys())):
            raise ValueError(
                "Invalid arguments provided for plotter (required: %s)", self.accepted_data
            )
        data = self.get_arg_data(kwargs)
        return self.function(function_input, **data)
