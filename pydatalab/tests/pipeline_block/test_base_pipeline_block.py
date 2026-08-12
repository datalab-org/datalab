from pathlib import Path
from unittest import mock

from pydatalab.config import CONFIG
from pydatalab.pipeline_block.base import DataBlockDefaults
from pydatalab.pipeline_block.block_manager import PipelineBlockManager, _perform_operations
from pydatalab.pipeline_block.pipeline import Pipeline
from pydatalab.pipeline_block.utils import generate_js_callback_single_float_parameter


def test_base_block():
    block_manager = PipelineBlockManager()
    block_manager.register_block(Pipeline(), DataBlockDefaults())
    block = block_manager.create_block_data("DataBlock", item_id="test-id")
    test_event = {"event_name": "null_event", "kwargs": {"a": 1, "b": 2, "c": 1.2, "d": "string"}}
    block_manager.process_events(block, test_event)
    assert block["kwargs"]["a"] == 1
    assert block["kwargs"]["b"] == 2
    assert block["kwargs"]["c"] == 1.2
    assert block["kwargs"]["d"] == "string"


def test_callback():
    callback = generate_js_callback_single_float_parameter(
        "set_wavelength", "wavelength", block_id="test", throttled=False
    )
    assert (
        callback
        == """const block_event = new CustomEvent('block-event', {
    detail: {
        block_id: 'test',
        event_name: 'set_wavelength',
        wavelength: (cb_obj.value ?? cb_obj.text),
    }, bubbles: true
});
document.dispatchEvent(block_event);"""
    )


@mock.patch("pydatalab.pipeline_block.block_manager.get_file_info_by_id")
def test_file_acceptance_logic(get_file_info_by_id):
    get_file_info_by_id.return_value = {
        "location": "TEST_FILE_INFO.txt",
        "checksums": "TEST_CHECKSUM",
    }
    pipeline_mock = Pipeline()
    pipeline_mock.perform_entire_pipeline = mock.MagicMock(return_value=None)
    block_data = {"file_id": "12345678"}

    _perform_operations(
        DataBlockDefaults(multi_file=False, accepted_file_extensions=(".txt", ".csv")),
        pipeline_mock,
        block_data,
    )

    assert pipeline_mock.perform_entire_pipeline.is_called
    assert pipeline_mock.perform_entire_pipeline.call_count == 1
    pipeline_mock.perform_entire_pipeline.assert_called_once_with(
        data=block_data,
        file_folder=Path(CONFIG.FILE_DIRECTORY),
        files=[Path("TEST_FILE_INFO.txt")],
        checksums=["TEST_CHECKSUM"],
    )


@mock.patch("pydatalab.pipeline_block.block_manager.get_file_info_by_id")
@mock.patch("pydatalab.pipeline_block.block_manager.LOGGER")
def test_should_fail_file_type(logger, get_file_info_by_id):
    get_file_info_by_id.return_value = {
        "location": "TEST_FILE_INFO.exe",
        "checksums": "TEST_CHECKSUM",
    }
    pipeline_mock = Pipeline()
    pipeline_mock.perform_entire_pipeline = mock.MagicMock(return_value=None)
    block_data = {"file_id": "12345678"}
    result = _perform_operations(
        DataBlockDefaults(multi_file=False, accepted_file_extensions=(".txt", ".csv")),
        pipeline_mock,
        block_data,
    )
    assert pipeline_mock.perform_entire_pipeline.call_count == 0
    assert result is None
    assert logger.warning.call_count == 1
    logger.warning.assert_called_once_with(
        "File with extension `%s` is not an acceptable file extension, (acceptable parsers: `%s`)",
        ".exe",
        (".txt", ".csv"),
    )
