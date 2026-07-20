import inspect
import pathlib
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any

import pandas as pd

from pydatalab.logger import LOGGER

__all__ = ["ParserStage", "ProcessorStage", "PlotterStage", "EventStage"]


class Stage(Enum):
    PARSER = "parser"
    PROCESSOR = "processor"
    PLOTTER = "plotter"
    EVENT = "event"
    DEFAULT = "default"


class BlockStage(ABC):
    stage: Stage
    """Informs the user what the stage of this function is"""

    function: "Callable[[Any], Any]"
    """Generic function to call"""

    accepted_data: list[str] = []
    """Whether the parser accepts a data dictionary"""

    list_df_input: bool
    """Whether the stage takes lists of dfs or just an individual df"""  #

    def compute_expected_data(self) -> None:
        self.accepted_data = list(inspect.signature(self.function).parameters.keys())[1:]

    def check_args(self, input_args_names: list[str]):
        return (
            self.accepted_data
            or set(self.accepted_data) & set(input_args_names) == self.accepted_data
        )

    def get_arg_data(self, input_args: dict[str, Any]) -> dict[str, Any]:
        common_args = set(self.accepted_data) & set(input_args.keys())
        return {arg: input_args[arg] for arg in common_args}

    def __init__(
        self,
        function,
        list_df_input: bool = False,
        accepted_data=None,
        stage: Stage = Stage.DEFAULT,
    ):
        self.function = function
        self.accepts_data = accepted_data
        self.stage = stage
        if accepted_data is None:
            self.compute_expected_data()
        self.list_df_input = list_df_input

    @abstractmethod
    def perform(self, function_input: Any, *args: Any, **kwargs: Any) -> Any:
        pass


class ParserStage(BlockStage):
    function: "Callable[[str|pathlib.Path], pd.DataFrame]"
    """The parser stage"""

    file_extension: list[str]
    """The valid file extension for this parser"""

    def __init__(
        self,
        function: "Callable[[str|pathlib.Path], pd.DataFrame]",
        file_extension: list[str] | str,
    ):
        """
        :param function: takes the function to call. Can be a function taking in a path on its own or with a dict.
        :param file_extension: The file extension for this parser stage, * indicates that this parser attempts to parse all files.
        """
        super().__init__(function, stage=Stage.PARSER)
        if type(file_extension) is str:
            self.file_extension = [file_extension]
        elif type(file_extension) is list:
            self.file_extension = file_extension
        else:
            raise TypeError("file_extension must be str or list")

    def validate_input(self, path: pathlib.Path) -> bool:
        """
        Checks whether the path extension is a valid file extension,
        and also has a wild card *, to show that a parser accepts all extensions
        :param path: The path to check
        """
        return (
            "".join(path.suffixes) in self.file_extension
            or path.suffix in self.file_extension
            or "*" in self.file_extension
        )

    def perform(self, function_input: pathlib.Path, *args, **kwargs) -> "pd.DataFrame | None":

        if not self.validate_input(function_input):
            LOGGER.warning("Invalid file extension for this particular parser stage")
            return None
        else:
            result = self.function(function_input)
        result.attrs["original_filename"] = function_input.name
        return result


class ProcessorStage(BlockStage):
    function: "Callable[..., pd.DataFrame|list[pd.DataFrame]]"
    """The processor stage function type"""

    def __init__(
        self,
        function: "Callable[[list[pd.DataFrame]|pd.DataFrame, dict], pd.DataFrame|list[pd.DataFrame]]",
        list_df_input: bool = False,
        accepted_data: list[str] | None = None,
    ):
        super().__init__(
            function, list_df_input, accepted_data=accepted_data, stage=Stage.PROCESSOR
        )

    def perform(
        self, function_input: "list[pd.DataFrame]|pd.DataFrame", *args, **kwargs
    ) -> "pd.DataFrame | list[pd.DataFrame]":

        # check the input to make sure that it matches the required input types
        if not self.check_args(list(kwargs.keys())):
            raise ValueError(
                "Invalid arguments provided for processor (required: %s)", self.accepted_data
            )
        data = self.get_arg_data(kwargs)
        if type(function_input) is not list and self.list_df_input:
            LOGGER.warning("Invalid input type for processor stage, forcing the input to be a list")
            function_input = [function_input]
        return self.function(function_input, **data)


class PlotterStage(BlockStage):
    function: "Callable[..., Any]"
    """The plotter stage"""

    def __init__(
        self,
        function: "Callable[[pd.DataFrame|list[pd.DataFrame]], Any]|Callable[[pd.DataFrame|list[pd.DataFrame], dict], Any]",
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


class EventStage(BlockStage):
    """Stages for events"""

    function: "Callable[..., None]"
    """The event stage function, takes the data dictionary and any amount of **args"""

    def __init__(self, function: "Callable[..., None]"):
        """
        :param function: The event stage function, takes the data dictionary and any amount of **args
        """
        super().__init__(function, stage=Stage.EVENT)

    def perform(self, function_input: dict, *args, **kwargs) -> None:
        kwargs.pop("block_id", None)
        self.function(function_input, **kwargs)
