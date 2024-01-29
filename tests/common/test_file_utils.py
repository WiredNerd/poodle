from __future__ import annotations

from unittest import mock

import pytest
from wcmatch.pathlib import Path

from poodle.common import file_utils
from poodle.common.config import PoodleConfigData


@pytest.fixture()
def mock_path():
    with mock.patch("poodle.common.file_utils.Path") as mock_path:
        yield mock_path


@pytest.fixture()
def mock_logger():
    with mock.patch("poodle.common.file_utils.logger") as mock_logger:
        yield mock_logger


def test_logger():
    assert file_utils.logger.name == "poodle.common.file_utils"


class TestFilesListForFolder:
    def test_files_list_for_folder(self, mock_path, mock_logger):
        files = [
            Path("src/project/file_1.py"),
            Path("src/project/file_test_2.py"),
        ]
        mock_folder = mock.MagicMock()
        mock_folder.rglob.return_value = iter(files)
        mock_path.return_value = mock_folder
        in_folder = mock.MagicMock()

        assert (
            file_utils.files_list_for_folder(
                folder=in_folder,
                match_glob="*.py",
                flags=4,
                filter_globs=["test_*.py"],
            )
            == files
        )

        mock_folder.rglob.assert_called_with("*.py", flags=4, exclude=["test_*.py"])
        mock_logger.debug.assert_any_call(
            "files_list_for_folder folder=%s, match_glob=%s filter_globs=%s",
            in_folder,
            "*.py",
            ["test_*.py"],
        )
        mock_logger.debug.assert_any_call(
            "files_list_for_folder results: folder=%s files=%s",
            in_folder,
            files,
        )


class TestFilesListForSourceFolders:
    @mock.patch("poodle.common.file_utils.files_list_for_folder")
    def test_files_list_for_source_folders(self, files_list_for_folder):
        config_data = PoodleConfigData()
        config_data.source_folders = [Path("src"), Path("lib")]

        assert file_utils.files_list_for_source_folders(config_data) == {
            Path("src"): files_list_for_folder.return_value,
            Path("lib"): files_list_for_folder.return_value,
        }

        files_list_for_folder.assert_has_calls(
            [
                mock.call(
                    folder=Path("src"),
                    match_glob="*",
                    flags=config_data.file_copy_flags,
                    filter_globs=config_data.file_copy_filters,
                ),
                mock.call(
                    folder=Path("lib"),
                    match_glob="*",
                    flags=config_data.file_copy_flags,
                    filter_globs=config_data.file_copy_filters,
                ),
            ]
        )


class TestCreateTempZips:
    @mock.patch("poodle.common.file_utils.files_list_for_source_folders")
    @mock.patch("poodle.common.file_utils.ZipFile")
    def test_create_temp_zips(self, ZipFile, files_list_for_source_folders, mock_logger):  # noqa: N803
        config_data = mock.MagicMock(work_folder=mock.MagicMock())
        work_folder = config_data.work_folder
        next_num = mock.MagicMock()
        next_num.side_effect = ["1", "2"]

        files_list_for_source_folders.return_value = {
            Path("example_1"): [Path("file_1.py")],
            Path("example_2"): [Path("file_2.py")],
        }

        work_folder.__truediv__.side_effect = [
            Path("temp/src-1.zip"),
            Path("temp/src-2.zip"),
        ]

        assert file_utils.create_temp_zips(config_data, next_num) == {
            Path("example_1"): Path("temp/src-1.zip"),
            Path("example_2"): Path("temp/src-2.zip"),
        }

        work_folder.mkdir.assert_called_with(parents=True, exist_ok=True)
        files_list_for_source_folders.assert_called_with(config_data)
        work_folder.__truediv__.assert_has_calls(
            [
                mock.call("src-1.zip"),
                mock.call("src-2.zip"),
            ]
        )
        mock_logger.info.assert_any_call("Creating zip file: %s", Path("temp/src-1.zip"))
        mock_logger.info.assert_any_call("Creating zip file: %s", Path("temp/src-2.zip"))

        ZipFile.assert_any_call(Path("temp/src-1.zip"), "w")
        ZipFile.assert_any_call(Path("temp/src-2.zip"), "w")
        target_zip = ZipFile.return_value.__enter__.return_value

        mock_logger.info.assert_any_call("Adding file: %s", Path("file_1.py"))
        mock_logger.info.assert_any_call("Adding file: %s", Path("file_2.py"))

        target_zip.write.assert_has_calls(
            [
                mock.call(Path("file_1.py")),
                mock.call(Path("file_2.py")),
            ]
        )


class TestDeleteFolder:
    @pytest.fixture()
    def shutil(self):
        with mock.patch("poodle.common.file_utils.shutil") as shutil:
            yield shutil

    def test_delete_folder_exists(self, shutil, mock_logger):
        folder = mock.MagicMock()
        folder.exists.return_value = True

        config_data = PoodleConfigData()
        config_data.skip_delete_folder = False

        file_utils.delete_folder(folder, config_data)

        mock_logger.info.assert_called_once_with("delete %s", folder)
        shutil.rmtree.assert_called_once_with(folder)

    def test_delete_folder_exists_skip(self, shutil, mock_logger):
        folder = mock.MagicMock()
        folder.exists.return_value = True

        config_data = PoodleConfigData()
        config_data.skip_delete_folder = True

        file_utils.delete_folder(folder, config_data)

        mock_logger.info.assert_not_called()
        shutil.rmtree.assert_not_called()

    def test_delete_folder_not_exists(self, shutil, mock_logger):
        folder = mock.MagicMock()
        folder.exists.return_value = False

        config_data = PoodleConfigData()
        config_data.skip_delete_folder = False

        file_utils.delete_folder(folder, config_data)

        mock_logger.info.assert_not_called()
        shutil.rmtree.assert_not_called()
