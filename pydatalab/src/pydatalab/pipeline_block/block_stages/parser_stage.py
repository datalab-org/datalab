import pathlib
from collections.abc import Callable
from typing import Any

import pandas as pd

from pydatalab.logger import LOGGER
from pydatalab.pipeline_block.block_stages.abstract_stage import BlockStage, Stage


class ParserStage(BlockStage):
    function: "Callable[[str|pathlib.Path], tuple[pd.DataFrame, dict]|pd.DataFrame]"
    """The parser stage"""

    file_extension: list[str]
    """The valid file extension for this parser"""

    def __init__(
        self,
        function: "Callable[[str|pathlib.Path], tuple[pd.DataFrame, dict]|pd.DataFrame]",
        file_extension: list[str] | str,
        caching=True,
    ):
        """
        :param function: takes the function to call. Can be a function taking in a path on its own or with a dict.
        :param file_extension: The file extension for this parser stage, * indicates that this parser attempts to parse all files.
        """
        super().__init__(function, stage=Stage.PARSER, caching=caching)
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

    def perform(self, function_input: pathlib.Path, *args, **kwargs) -> "tuple[Any, Any]":

        if not self.validate_input(function_input):
            LOGGER.warning("Invalid file extension for this particular parser stage")
            return None, None
        else:
            value = self.function(function_input)
            if type(value) is tuple:
                df, data = value
            else:
                df = value
                data = {}
        if data.get("metadata", None) is None:
            data["metadata"] = {}
        data["metadata"]["original_filenames"] = [function_input.name]
        return df, data
