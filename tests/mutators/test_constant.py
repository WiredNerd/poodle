import ast
from unittest import mock

import pytest

from poodle.mutators.constant import KeywordMutator, NumberMutator, StringMutator


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


class TestNumberMutator:
    def test_name(self):
        assert NumberMutator.mutator_name == "Number"

    @pytest.mark.parametrize(
        ("source", "mutants"),
        [
            ("3", ["4", "2"]),
            ("0o3", ["4", "2"]),
            ("0x3", ["4", "2"]),
            ("0b11", ["4", "2"]),
            ("3j", ["4j", "2j"]),
            ("0.0", ["1.0"]),
            ("1.2", ["2.4", "0.6"]),
            ("True", []),
            ("False", []),
        ],
    )
    def test_create_mutations(self, source, mutants, mock_echo):
        mutator = NumberMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        file_mutants = mutator.create_mutations(ast.parse(source))

        assert len(file_mutants) == len(mutants)

        for i in range(len(mutants)):
            assert file_mutants[i].lineno == 1
            assert file_mutants[i].end_lineno == 1
            assert file_mutants[i].col_offset == 0
            assert file_mutants[i].end_col_offset == len(source)
            assert file_mutants[i].text == mutants[i]


class TestStringMutator:
    def test_name(self):
        assert StringMutator.mutator_name == "String"

    def test_create_mutations_double_quote(self, mock_echo):
        mutator = StringMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        file_mutants = mutator.create_mutations(ast.parse('a = "Poodle\'s Name"'))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 19
        assert file_mutants[0].text == '"XXPoodle\'s NameXX"'

    def test_create_mutations_single_quote(self, mock_echo):
        mutator = StringMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        file_mutants = mutator.create_mutations(ast.parse("a = 'Hello \"Poodle\"'"))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 20
        assert file_mutants[0].text == "'XXHello \"Poodle\"XX'"

    def test_create_mutations_doc(self, mock_echo):
        mutator = StringMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        assert mutator.create_mutations(ast.parse('"""Poodle\'s Name"""')) == []


class TestKeywordMutator:
    def test_name(self):
        assert KeywordMutator.mutator_name == "Keyword"

    @pytest.mark.parametrize(
        ("source", "mutants"),
        [
            ("continue", ["break"]),
            ("break", ["continue"]),
            ("False", ["True"]),
            ("True", ["False"]),
            ("None", ["' '"]),
        ],
    )
    def test_create_mutations(self, source, mutants, mock_echo):
        mutator = KeywordMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        file_mutants = mutator.create_mutations(ast.parse(source))

        assert len(file_mutants) == len(mutants)

        for i in range(len(mutants)):
            assert file_mutants[i].lineno == 1
            assert file_mutants[i].end_lineno == 1
            assert file_mutants[i].col_offset == 0
            assert file_mutants[i].end_col_offset == len(source)
            assert file_mutants[i].text == mutants[i]

    def test_annotations(self, mock_echo):
        mutator = KeywordMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)
        module = "\n".join(  # noqa: FLY002
            [
                "def example(y:str | None)->str | None:",
                "    x: str | None = y",
                "    return y",
            ],
        )
        file_mutants = mutator.create_mutations(ast.parse(module))

        assert file_mutants == []
