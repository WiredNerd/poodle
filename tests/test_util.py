from pathlib import Path
from unittest import mock

import pytest

from poodle import util
from poodle.data_types import PoodleWork
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def mock_logger():
    with mock.patch("poodle.util.logger") as logger:
        yield logger


def test_logger():
    assert util.logger.name == "poodle.util"


class TestFilesList:
    def test_files_list_for_folder(self, mock_logger):
        mock_folder = mock.MagicMock()
        mock_folder.rglob.return_value = (
            Path("src/project/file_1.py"),
            Path("src/project/file_test_2.py"),
            Path("src/project/__pycache__/file_1.pyc"),
            Path("src/project/__pycache__/file_test_2.pyc"),
        )
        files = util.files_list_for_folder("*.py", [r"^test_.*\.py$", r"_test\.py$", r"^__pycache__$"], mock_folder)
        assert files == [
            Path("src/project/file_1.py"),
            Path("src/project/file_test_2.py"),
        ]
        mock_folder.rglob.assert_called_with("*.py")
        mock_logger.debug.assert_any_call(
            "files_list_for_folder glob=%s filter_regex=%s folder=%s",
            "*.py",
            [r"^test_.*\.py$", r"_test\.py$", r"^__pycache__$"],
            mock_folder,
        )
        mock_logger.debug.assert_any_call(
            "files_list_for_folder results: folder=%s files=%s",
            mock_folder,
            files,
        )

    def test_files_list_for_source_folders(self, mock_logger):
        mock_folder_1 = mock.MagicMock()
        mock_folder_1.rglob.return_value = (
            Path("file_1.py"),
            Path("test_file_1.py"),
        )
        mock_folder_2 = mock.MagicMock()
        mock_folder_2.rglob.return_value = (
            Path("file_test_2.py"),
            Path("file_2_test.py"),
        )
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[mock_folder_1, mock_folder_2],
                file_copy_filters=[r"^test_.*\.py$", r"_test\.py$"],
            )
        )
        assert util.files_list_for_source_folders(work) == {
            mock_folder_1: [Path("file_1.py")],
            mock_folder_2: [Path("file_test_2.py")],
        }
        mock_folder_1.rglob.assert_called_with("*")
        mock_folder_2.rglob.assert_called_with("*")
        mock_logger.debug.assert_has_calls(
            [
                mock.call(
                    "files_list_for_folder glob=%s filter_regex=%s folder=%s",
                    "*",
                    [r"^test_.*\.py$", r"_test\.py$"],
                    mock_folder_1,
                ),
                mock.call(
                    "files_list_for_folder results: folder=%s files=%s",
                    mock_folder_1,
                    [Path("file_1.py")],
                ),
                mock.call(
                    "files_list_for_folder glob=%s filter_regex=%s folder=%s",
                    "*",
                    [r"^test_.*\.py$", r"_test\.py$"],
                    mock_folder_2,
                ),
                mock.call(
                    "files_list_for_folder results: folder=%s files=%s",
                    mock_folder_2,
                    [Path("file_test_2.py")],
                ),
            ]
        )

    @mock.patch("poodle.util.files_list_for_source_folders")
    @mock.patch("poodle.util.ZipFile")
    def test_create_temp_zips(self, ZipFile, files_list_for_source_folders, mock_logger):  # noqa: N803
        work_folder = mock.MagicMock()
        work_folder.__truediv__.side_effect = lambda x: Path(x)
        files_list_for_source_folders.return_value = {
            Path("example_1"): [Path("file_1.py")],
            Path("example_2"): [Path("file_2.py")],
        }
        work = PoodleWork(
            config=PoodleConfigStub(
                work_folder=work_folder,
            )
        )
        util.create_temp_zips(work)
        work_folder.mkdir.assert_called_with(parents=True, exist_ok=True)
        files_list_for_source_folders.assert_called_with(work)
        mock_logger.info.assert_has_calls(
            [
                mock.call("Creating zip file: %s", Path("src-1.zip")),
                mock.call("Creating zip file: %s", Path("src-2.zip")),
            ]
        )
        assert work.folder_zips == {
            Path("example_1"): Path("src-1.zip"),
            Path("example_2"): Path("src-2.zip"),
        }
        ZipFile.assert_any_call(Path("src-1.zip"), "w")
        ZipFile.assert_any_call(Path("src-2.zip"), "w")
        target_zip = ZipFile.return_value.__enter__.return_value
        target_zip.write.assert_has_calls(
            [
                mock.call(Path("file_1.py")),
                mock.call(Path("file_2.py")),
            ]
        )


class TestDynamicImport:
    def test_dynamic_import(self, mock_logger):
        runner = util.dynamic_import("poodle.runners.command_line.runner")
        import poodle.runners.command_line

        assert runner is poodle.runners.command_line.runner

        mock_logger.debug.assert_called_with("Import object: %s", "poodle.runners.command_line.runner")


class TestPrint:
    def test_pprint_str(self):
        assert util.pprint_str({"key1": "value1", "key2": "value2"}) == "{'key1': 'value1', 'key2': 'value2'}\n"

    @mock.patch("poodle.util.StringIO")
    @mock.patch("poodle.util.pprint")
    def test_pprint_str_mock(self, pprint, StringIO):  # noqa: N803
        obj = {"key1": "value1", "key2": "value2"}
        util.pprint_str(obj)
        out = StringIO.return_value
        pprint.assert_called_with(obj, stream=out, width=150)
