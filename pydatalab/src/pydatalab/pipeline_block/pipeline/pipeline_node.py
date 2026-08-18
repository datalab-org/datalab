import warnings
from pathlib import Path
from typing import Any

from pydatalab.logger import LOGGER
from pydatalab.pipeline_block.block_stages.abstract_stage import BlockStage
from pydatalab.pipeline_block.utils import merge_dictionaries

__all__ = ["PipelineNode", "OutputRoot", "FileInputLeaf"]


def merge_inputs(total_input) -> dict[str, Any]:
    if len(total_input) == 1:
        return total_input[0]
    combined_input: dict = {
        "upstream_cache_key": "",
        "folder": [],
        "function_input": [],
        "data": {},
    }
    for single_input in total_input:
        combined_input["upstream_cache_key"] += "|" + single_input["upstream_cache_key"]
        combined_input["folder"] = single_input["folder"]
        if type(single_input["function_input"]) is not list:
            single_input["function_input"] = [single_input["function_input"]]
        combined_input["function_input"].extend(single_input["function_input"])
        merge_dictionaries(combined_input["data"], single_input["data"])
    return combined_input


def accumulate_data(next_input: dict, old_input: dict):
    next_input["data"] = merge_dictionaries(old_input["data"], next_input["data"])
    return next_input


class PipelineNode:
    def __init__(self, stage: BlockStage, parent_node, number_of_inputs: int) -> None:
        self.stage: BlockStage = stage
        self.parent_node: PipelineNode = parent_node  # parent of this Node
        self.total_input = []
        self.number_of_inputs = number_of_inputs
        self.output: Any = None

    def notify_more_inputs_are_coming(self, amount: int):
        """
        In cases where there are more inputs than previously estimated when building the graph.
        :param amount: Number of additional inputs
        :return: Nothing.
        """
        self.number_of_inputs += amount - 1

    def notify_no_inputs_are_coming(self):
        """
        Informs the node that no inputs are coming from a node further down the graph.
        :return: Nothing
        """
        self.number_of_inputs -= 1
        LOGGER.debug(
            "number of inputs reduced to %s, for %s, with function name: %s",
            self.number_of_inputs,
            self.stage.stage.value,
            self.stage.function.__name__,
        )
        if self.number_of_inputs == 0:
            LOGGER.warning(
                "No inputs for %s, with function name: %s",
                self.stage.stage.value,
                self.stage.function.__name__,
            )
            self.parent_node.notify_no_inputs_are_coming()
        else:
            self.send_output_if_enough_data()

    def register_input(self, function_input):
        """
        Gives the node new data which then can be fed to the stage to perform the relevant action.
        :param function_input: The input to the stage function
        :return: Nothing
        """
        if type(function_input) is not list:
            function_input = [function_input]
        self.total_input.extend(function_input)

        self.send_output_if_enough_data()

    def send_output_if_enough_data(self):
        if len(self.total_input) >= self.number_of_inputs:
            LOGGER.debug(
                "Firing %s, with function name: %s",
                self.stage.stage.value,
                self.stage.function.__name__,
            )
            try:
                if not self.stage.list_df_input:
                    self.output = []
                    for singular_input in self.total_input:
                        self.output.append(
                            accumulate_data(
                                self.stage.perform_with_optional_cache(**singular_input),
                                singular_input,
                            )
                        )
                else:
                    final_input = merge_inputs(self.total_input)
                    self.output = accumulate_data(
                        self.stage.perform_with_optional_cache(**final_input), final_input
                    )
            except Exception as exc:
                warnings.warn(f"This {self.stage.stage} stage failed with error: {exc}")
                # Tell parent no inputs are coming
                self.parent_node.notify_no_inputs_are_coming()
                self.output = None
            else:
                if output_length := len(self.output) != 1:
                    self.parent_node.notify_more_inputs_are_coming(output_length)
                self.parent_node.register_input(self.output)

    def get_input_file_type(self):
        return set(self.stage.file_extension)

    def add_pipeline(self, stage_list: list[list[BlockStage]]) -> list:
        if len(stage_list) == 0:
            self.number_of_inputs = 1
            return [FileInputLeaf(parent_node=self, file_input_type=self.get_input_file_type())]
        endpoints = []
        for stage in stage_list[-1]:
            if (
                set(stage.file_extension).issuperset(self.get_input_file_type())
                or "*" in self.get_input_file_type()
            ):
                next_node = PipelineNode(stage, self, 0)
                endpoints.extend(next_node.add_pipeline(stage_list[:-1]))
                self.number_of_inputs += 1
        return endpoints


class FileInputLeaf:
    def __init__(self, parent_node: PipelineNode, file_input_type: set[str]):
        self.parent_node: PipelineNode = parent_node
        self.file_input_type: set[str] = file_input_type
        self.list_of_files: list = []

    def register_files_and_execute(
        self,
        list_of_files: list[str | Path],
        list_of_checksums: list[str],
        file_folder: str | Path,
        data,
    ):
        if not list_of_files:
            self.parent_node.notify_no_inputs_are_coming()
            return
        self.list_of_files = list_of_files
        self.parent_node.notify_more_inputs_are_coming(len(list_of_files))
        for index, file in enumerate(self.list_of_files):
            function_input = {
                "upstream_cache_key": list_of_checksums[index],
                "folder": file_folder,
                "function_input": file,
                "data": data,
            }
            self.parent_node.register_input(function_input)


class OutputRoot:
    def __init__(self):
        self.output = []
        self.number_of_inputs = 0

    def register_input(self, function_input: dict[str, Any]) -> None:
        if type(function_input) is not list:
            function_input = [function_input]
        self.output.extend(function_input)

    def get_result(self):
        return merge_inputs(self.output)

    def notify_more_inputs_are_coming(self, amount: int):
        self.number_of_inputs += amount - 1

    def notify_no_inputs_are_coming(self):
        self.number_of_inputs -= 1

    def add_pipeline(self, stage_list: list[list[BlockStage]]) -> list:
        endpoints = []
        for stage in stage_list[-1]:
            next_node = PipelineNode(stage, self, 0)
            endpoints.extend(next_node.add_pipeline(stage_list[:-1]))
            self.number_of_inputs += 1
        return endpoints
