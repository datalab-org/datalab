from collections.abc import Callable
from typing import Any

import pandas as pd

from pydatalab.logger import LOGGER
from pydatalab.pipeline_block.block_stages.abstract_stage import BlockStage, Stage


class ProcessorStage(BlockStage):
    function: "Callable[..., tuple[pd.DataFrame|list[pd.DataFrame], dict|list[dict]]]"
    """The processor stage function type"""

    def validate_input(self, function_input: Any) -> bool:
        # TODO allow user to have their own validation function or list of columns that it must be.
        return function_input is not None and (
            (type(function_input) is pd.DataFrame and (not function_input.empty))
            or (type(function_input) is list and self.list_df_input)
        )

    def __init__(
        self,
        function: "Callable[..., tuple[pd.DataFrame|list[pd.DataFrame], dict|list[dict]]]",
        list_df_input: bool = False,
        caching: bool = True,
        accepted_data: list[str] | None = None,
        file_extension: str | list[str] = "*",
    ):
        super().__init__(
            function,
            list_df_input,
            accepted_data=accepted_data,
            stage=Stage.PROCESSOR,
            caching=caching,
            file_extension=file_extension,
        )

    def perform(
        self, function_input: "list[pd.DataFrame]|pd.DataFrame", *args, **kwargs
    ) -> tuple[Any, Any | None]:

        # check the input to make sure that it matches the required input types
        if not self.check_args(list(kwargs.keys())):
            raise ValueError(
                "Invalid arguments provided for processor (required: %s, received: %s)",
                self.accepted_data,
                list(kwargs.keys()),
            )
        data = self.get_arg_data(kwargs)
        if type(function_input) is not list and self.list_df_input:
            LOGGER.warning("Invalid input type for processor stage, forcing the input to be a list")
            function_input = [function_input]
        elif type(function_input) is list and not self.list_df_input:
            raise ValueError(
                "Invalid input type for processor stage, input type should not be a list"
            )
        result = self.function(function_input, **data)
        if type(result) is tuple:
            df, data = result
        else:
            df = result
            data = None
        return df, data
