import hashlib
import inspect
import json
import pathlib
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from io import BytesIO
from typing import Any

import pandas as pd
import pyarrow

from pydatalab.logger import LOGGER

__all__ = ["ParserStage", "ProcessorStage", "PlotterStage", "EventStage"]


class Stage(Enum):
    PARSER = "parser"
    PROCESSOR = "processor"
    PLOTTER = "plotter"
    EVENT = "event"
    DEFAULT = "default"


def _load_from_cache(file_name) -> list[Any]:
    """
    This functions loads the file from a parquet cache into a pandas dataframe with associated metadata.
    parameters:
    file_name: str the filename of the parquet file
    """
    LOGGER.info("Loading %s from cache.", file_name)
    cached_dfs = pd.read_parquet(file_name)
    returned_dfs = []
    order = []
    for index, row in cached_dfs.iterrows():
        reader = pyarrow.BufferReader(row["Payloads"])
        df = pd.read_feather(reader)
        df.attrs = json.loads(row["Metadata"])
        returned_dfs.append(df)
        order.append(row["Index"])
    returned_dfs = [x for _, x in sorted(zip(order, returned_dfs), key=lambda p: p[0])]
    return returned_dfs


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
            not self.accepted_data
            or set(self.accepted_data) & set(input_args_names) == self.accepted_data
        )

    def get_arg_data(self, input_args: dict[str, Any]) -> dict[str, Any]:
        common_args = set(self.accepted_data) & set(input_args.keys())
        return {arg: input_args[arg] for arg in common_args}

    def _create_and_save_to_cache(
        self, file_name, function_input, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Any:
        """
        Creates the df by performing the block_stage operations and then caches the file.
        """
        LOGGER.info("Loading and saving the output to cache.")
        # result is not cached, needs to be computed and cached
        original_result = self.perform(function_input, *args, **kwargs)

        results = original_result.copy()

        if type(results) is not list:
            results = [results]
        indices = []
        attrs = []
        payloads = []
        for index, result in enumerate(results):
            indices.append(index)
            attrs.append(json.dumps(result.attrs))
            with BytesIO() as buf:
                result.to_feather(buf)
                payloads.append(buf.getvalue())
        cacheable_result = pd.DataFrame()
        cacheable_result["Index"] = indices
        cacheable_result["Metadata"] = attrs
        cacheable_result["Payloads"] = payloads
        cacheable_result.to_parquet(file_name)
        return original_result

    @abstractmethod
    def validate_input(self, function_input: Any) -> bool:
        pass

    def perform_with_cache(
        self, upstream_cache_key, folder, function_input: Any, *args: Any, **kwargs: Any
    ) -> "tuple[str, pd.DataFrame | list[pd.DataFrame]]| tuple[None, None]":
        if not self.validate_input(function_input):
            LOGGER.info("This input is not valid for this %s stage", self.stage)
            return None, None
        LOGGER.info("Performing %s stage with cache.", self.stage)
        if self.stage == Stage.PLOTTER:
            raise ValueError("Plotter Stage is not cached")
        elif self.stage == Stage.EVENT:
            raise ValueError("Event Stage is not cached")
        arg_data = self.get_arg_data(kwargs)

        cache_key_components = [upstream_cache_key, self.stage, self.function.__name__]
        cache_key_components.extend(arg_data.values())

        cache_key = hashlib.md5(  # noqa: S324
            "|".join(sorted(str(component) for component in cache_key_components)).encode()
        ).hexdigest()[:10]

        file_name = folder / f"{cache_key}.parquet"

        if file_name.exists():
            return cache_key, _load_from_cache(file_name)
        else:
            return cache_key, self._create_and_save_to_cache(
                file_name, function_input, args, kwargs
            )

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
        function: "Callable[[str|pathlib.Path], pd.DataFrame]|Callable[[str], pd.DataFrame]",
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
        return path is not None and (
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

    def validate_input(self, function_input: Any) -> bool:
        # TODO allow user to have their own validation function or list of columns that it must be.
        return function_input is not None and (
            (type(function_input) is pd.DataFrame and (not function_input.empty))
            or (type(function_input) is list and self.list_df_input)
        )

    def __init__(
        self,
        function: "Callable[..., pd.DataFrame|list[pd.DataFrame]]",
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
