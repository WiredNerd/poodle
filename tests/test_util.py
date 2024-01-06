from pathlib import Path
from unittest import mock

import pytest

from poodle import util
from poodle.data_types import Mutant, MutantTrial, PoodleWork
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def mock_logger():
    with mock.patch("poodle.util.logger") as logger:
        yield logger


def test_logger():
    assert util.logger.name == "poodle.util"


class TestFilesList:
    @mock.patch("poodle.util.Path")
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
            util.files_list_for_folder(
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

    @mock.patch("poodle.util.Path")
    def test_files_list_for_source_folders(self, mock_path):
        files_1 = [
            Path("file_1.py"),
            Path("test_file_1.py"),
        ]
        files_2 = [
            Path("file_test_2.py"),
            Path("file_2_test.py"),
        ]
        mock_folder = mock.MagicMock()
        mock_folder.rglob.side_effect = [iter(files_1), iter(files_2)]
        mock_path.return_value = mock_folder

        mock_folder_1 = mock.MagicMock()
        mock_folder_2 = mock.MagicMock()

        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[mock_folder_1, mock_folder_2],
                file_copy_flags=0,
                file_copy_filters=["test_*.py", "*_test.py"],
            )
        )

        assert util.files_list_for_source_folders(work) == {
            mock_folder_1: files_1,
            mock_folder_2: files_2,
        }

        mock_path.assert_has_calls(
            [
                mock.call(mock_folder_1),
                mock.call().rglob("*", flags=0, exclude=["test_*.py", "*_test.py"]),
                mock.call(mock_folder_2),
                mock.call().rglob("*", flags=0, exclude=["test_*.py", "*_test.py"]),
            ]
        )
        mock_folder.rglob.assert_has_calls(
            [
                mock.call("*", flags=0, exclude=["test_*.py", "*_test.py"]),
                mock.call("*", flags=0, exclude=["test_*.py", "*_test.py"]),
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
                mock.call("Adding file: %s", Path("file_1.py")),
                mock.call("Creating zip file: %s", Path("src-2.zip")),
                mock.call("Adding file: %s", Path("file_2.py")),
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


class TestCalcTimeout:
    def test_calc_timeout(self):
        config = PoodleConfigStub(min_timeout=10, timeout_multiplier=10)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=2.01),
        }
        assert round(util.calc_timeout(config, clean_run_results), 1) == 20.1

    def test_calc_timeout_mult(self):
        config = PoodleConfigStub(min_timeout=10, timeout_multiplier=5)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=2.01),
        }
        assert round(util.calc_timeout(config, clean_run_results), 2) == round(10.05, 2)

    def test_calc_timeout_min(self):
        config = PoodleConfigStub(min_timeout=10, timeout_multiplier=10)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=0.1),
        }
        assert round(util.calc_timeout(config, clean_run_results), 1) == 10.0

    def test_calc_timeout_min_20(self):
        config = PoodleConfigStub(min_timeout=20, timeout_multiplier=10)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=0.1),
        }
        assert round(util.calc_timeout(config, clean_run_results), 1) == 20.0


class TestMutateLines:
    def test_mutate_lines(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=2,
            end_col_offset=13,
            text="Goodbye",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Hello World!",
            "3 Poodles are the best",
        ]
        assert util.mutate_lines(mutant, file_lines) == [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Goodbye!",
            "3 Poodles are the best",
        ]

    def test_mutate_lines_multi(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=4,
            end_col_offset=3,
            text="Goodbye, T",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Hello World!",
            "3 Poodles are the best",
            "4 Two are better than one",
        ]
        assert util.mutate_lines(mutant, file_lines) == [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Goodbye, Two are better than one",
        ]


class TestUnifiedDiff:
    def test_create_unified_diff(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=2,
            end_col_offset=13,
            text="Goodbye",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog\n",
            "2 Hello World!\n",
            "3 Poodles are the best\n",
        ]
        mutant.source_file.read_text.return_value.splitlines.return_value = file_lines
        mutant.source_file.__str__.return_value = "src/example.py"
        diff_str = (
            "--- src/example.py\n"
            "+++ [Mutant] src/example.py:2\n"
            "@@ -1,3 +1,3 @@\n"
            " 1 The quick brown fox jumps over the lazy dog\n"
            "-2 Hello World!\n"
            "+2 Goodbye!\n"
            " 3 Poodles are the best\n"
        )
        assert util.create_unified_diff(mutant) == diff_str

    def test_create_unified_diff_no_file(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=2,
            end_col_offset=13,
            text="Goodbye",
            source_folder=mock.MagicMock(),
            source_file=None,
        )
        assert util.create_unified_diff(mutant) is None


class TestDisplayPercent:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0.0014, "0.1%"),
            (0.0016, "0.1%"),
            (0.1239, "12.3%"),
            (0.12, "12%"),
            (0.1, "10%"),
            (0.99, "99%"),
            (0.999, "99.9%"),
            (0.9999, "99.9%"),
        ],
    )
    def test_display_percent(self, value, expected):
        assert util.display_percent(value) == expected
