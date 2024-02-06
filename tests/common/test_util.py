from unittest import mock

import pytest

from poodle.common import util
from poodle.common.data import Mutant


class TestPrint:
    def test_pprint_str(self):
        assert util.pprint_to_str({"key1": "value1", "key2": "value2"}) == "{'key1': 'value1', 'key2': 'value2'}\n"

    @mock.patch("poodle.common.util.StringIO")
    @mock.patch("poodle.common.util.pprint")
    def test_pprint_to_str_mock(self, pprint, StringIO):  # noqa: N803
        obj = {"key1": "value1", "key2": "value2"}
        util.pprint_to_str(obj)
        out = StringIO.return_value
        pprint.assert_called_with(obj, stream=out, width=150)


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
        mutant.source_file.read_text.assert_called_once_with("utf-8")
        mutant.source_file.read_text.return_value.splitlines.assert_called_once_with(keepends=True)

    def test_create_unified_diff_multiline(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=3,
            end_col_offset=22,
            text="Hello Poodle!\n3 Poodles are smart",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog\n",
            "2 Hello World!\n",
            "3 Poodles are the best!\n",
        ]
        mutant.source_file.read_text.return_value.splitlines.return_value = file_lines
        mutant.source_file.__str__.return_value = "src/example.py"
        diff_str = (
            "--- src/example.py\n"
            "+++ [Mutant] src/example.py:2\n"
            "@@ -1,3 +1,3 @@\n"
            " 1 The quick brown fox jumps over the lazy dog\n"
            "-2 Hello World!\n"
            "-3 Poodles are the best!\n"
            "+2 Hello Poodle!\n"
            "+3 Poodles are smart!\n"
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
