import hashlib
import inspect
import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow

from pydatalab.logger import LOGGER


class Stage(Enum):
    PARSER = "parser"
    PROCESSOR = "processor"
    PLOTTER = "plotter"
    EVENT = "event"
    DEFAULT = "default"


def _load_from_cache(file_name) -> tuple[list[Any], list[dict]]:
    """
    This functions loads the file from a parquet cache into a pandas dataframe with associated metadata.
    parameters:
    file_name: str the filename of the parquet file
    """
    LOGGER.info("Loading %s from cache.", file_name)
    cached_dfs = pd.read_parquet(file_name)
    returned_dfs = []
    metadata = []
    order = []
    for index, row in cached_dfs.iterrows():
        reader = pyarrow.BufferReader(row["Payloads"])
        df = pd.read_feather(reader)
        metadata = json.loads(row["Metadata"])
        returned_dfs.append(df)
        order.append(row["Index"])
    returned_dfs = [x for _, x in sorted(zip(order, returned_dfs), key=lambda p: p[0])]
    return returned_dfs, metadata


class BlockStage(ABC):
    stage: Stage
    """Informs the user what the stage of this function is"""

    function: "Callable[[Any], Any]"
    """Generic function to call"""

    accepted_data: list[str] = []
    """Whether the parser accepts a data dictionary"""

    list_df_input: bool
    """Whether the stage takes lists of dfs or just an individual df"""

    caching: bool = False
    """Whether the stage performs caching or not"""

    def compute_expected_data(self) -> None:
        self.accepted_data = list(inspect.signature(self.function).parameters.keys())[1:]

    def check_args(self, input_args_names: list[str]):
        return not self.accepted_data or (
            set(self.accepted_data) & set(input_args_names) == set(self.accepted_data)
        )

    def get_arg_data(self, input_args: dict[str, Any]) -> dict[str, Any]:
        common_args = set(self.accepted_data) & set(input_args.keys())
        return {arg: input_args[arg] for arg in common_args}

    @abstractmethod
    def validate_input(self, function_input: Any) -> bool:
        pass

    def _create_and_save_to_cache(
        self, file_name, function_input, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Any:
        """
        Creates the df by performing the block_stage operations and then caches the file.
        """
        LOGGER.info("Loading and saving the output to cache.")
        # result is not cached, needs to be computed and cached
        original_result, metadata = self.perform(function_input, *args, **kwargs)

        results = original_result.copy()

        if type(results) is not list:
            results = [results]
        indices = []
        metadata_list = [json.dumps(metadata)]
        payloads = []
        for index, result in enumerate(results):
            indices.append(index)

            with BytesIO() as buf:
                result.to_feather(buf)
                payloads.append(buf.getvalue())
        cacheable_result = pd.DataFrame()
        cacheable_result["Index"] = indices
        cacheable_result["Metadata"] = metadata_list
        cacheable_result["Payloads"] = payloads
        cacheable_result.to_parquet(file_name)
        return original_result, metadata

    def perform_with_optional_cache(
        self,
        upstream_cache_key,
        folder,
        function_input: Any,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> tuple[Any, Any, Any]:
        if self.caching:
            return self.perform_with_cache(
                upstream_cache_key, folder, function_input, *args, **kwargs
            )
        else:
            result = self.perform(function_input, *args, **kwargs)
            if type(result) is tuple:
                return "None", result[0], result[1]
            else:
                return "None", result, None

    def perform_with_cache(
        self, upstream_cache_key, folder: Path, function_input: Any, *args: Any, **kwargs: Any
    ) -> "tuple[str, pd.DataFrame | list[pd.DataFrame], list[dict]]| tuple[None, None, None]":
        if not self.validate_input(function_input):
            LOGGER.info("This input is not valid for this %s stage", self.stage)
            return None, None, None
        LOGGER.info("Performing %s stage with cache.", self.stage)
        if self.stage == Stage.PLOTTER:
            raise ValueError("Plotter Stage is not cached")
        elif self.stage == Stage.EVENT:
            raise ValueError("Event Stage is not cached")
        arg_data = self.get_arg_data(kwargs)

        # calculate hash components
        cache_key_components = [upstream_cache_key, self.stage, self.function.__name__]
        cache_key_components.extend(arg_data.values())

        cache_key = hashlib.md5(  # noqa: S324
            "|".join(sorted(str(component) for component in cache_key_components)).encode()
        ).hexdigest()[:10]

        file_name = folder / f"{cache_key}.parquet"
        # check if filename exists, then decides whether to retrieve cache based on it.
        resulting_data: tuple[pd.DataFrame | list[pd.DataFrame], list[dict]]
        if file_name.exists():
            resulting_data = _load_from_cache(file_name)
        else:
            resulting_data = self._create_and_save_to_cache(file_name, function_input, args, kwargs)
        return cache_key, resulting_data[0], resulting_data[1]

    def __init__(
        self,
        function,
        list_df_input: bool = False,
        accepted_data=None,
        stage: Stage = Stage.DEFAULT,
        caching: bool = caching,
    ):
        self.function = function
        self.accepts_data = accepted_data
        self.stage = stage
        self.caching = caching
        if accepted_data is None:
            self.compute_expected_data()
        self.list_df_input = list_df_input

    @abstractmethod
    def perform(self, function_input: Any, *args: Any, **kwargs: Any) -> Any:
        pass
