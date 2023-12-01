import ast
from unittest import mock

import pytest

from poodle.mutators.calls import (
    DecoratorMutator,
    DictArrayCallMutator,
    FunctionCallMutator,
    LambdaReturnMutator,
    ReturnMutator,
)


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


class TestFunctionCallMutator:
    def test_mutator_name(self):
        assert FunctionCallMutator.mutator_name == "FuncCall"

    def test_create_mutations(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = FunctionCallMutator(config=config, echo=mock_echo, other="value")
        file_mutants = mutator.create_mutations(ast.parse("y = ex_func(1)"))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 14
        assert file_mutants[0].text == "None"


class TestDictArrayCallMutator:
    def test_mutator_name(self):
        assert DictArrayCallMutator.mutator_name == "DictArray"

    def test_dict_call_mutator(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = DictArrayCallMutator(config=config, echo=mock_echo, other="value")
        file_mutants = mutator.create_mutations(ast.parse("y = d['a']"))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 10
        assert file_mutants[0].text == "None"

    def test_array_call_mutator(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = DictArrayCallMutator(config=config, echo=mock_echo, other="value")
        file_mutants = mutator.create_mutations(ast.parse("y = d[1]"))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 8
        assert file_mutants[0].text == "None"

    def test_skip_annotation_on_assign(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = DictArrayCallMutator(config=config, echo=mock_echo, other="value")
        file_mutants = mutator.create_mutations(ast.parse("y: list[str] = d"))

        assert file_mutants == []

    def test_skip_annotation_in_function(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = DictArrayCallMutator(config=config, echo=mock_echo, other="value")
        module = "\n".join(  # noqa: FLY002
            [
                "def example(y: list[str]):",
                "    return y",
            ],
        )
        file_mutants = mutator.create_mutations(ast.parse(module))

        assert file_mutants == []


class TestLambdaReturnMutator:
    def test_mutator_name(self):
        assert LambdaReturnMutator.mutator_name == "Lambda"

    def test_lambda_return_mutator(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = LambdaReturnMutator(config=config, echo=mock_echo, other="value")
        file_mutants = mutator.create_mutations(ast.parse("f = lambda x: x + 1"))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 19
        assert file_mutants[0].text == "lambda x: None"

    def test_lambda_returns_none(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = LambdaReturnMutator(config=config, echo=mock_echo, other="value")
        file_mutants = mutator.create_mutations(ast.parse("f = lambda x: None"))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 18
        assert file_mutants[0].text == "lambda x: ''"


class TestReturnMutator:
    def test_mutator_name(self):
        assert ReturnMutator.mutator_name == "Return"

    def test_return_mutator(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = ReturnMutator(config=config, echo=mock_echo, other="value")
        module = "\n".join(  # noqa: FLY002
            [
                "def example(y):",
                "    return y",
            ],
        )
        file_mutants = mutator.create_mutations(ast.parse(module))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 2
        assert file_mutants[0].end_lineno == 2
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 12
        assert file_mutants[0].text == "return None"

    def test_return_mutator_none(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = ReturnMutator(config=config, echo=mock_echo, other="value")
        module = "\n".join(  # noqa: FLY002
            [
                "def example(y):",
                "    return None",
            ],
        )
        file_mutants = mutator.create_mutations(ast.parse(module))

        assert len(file_mutants) == 1

        assert file_mutants[0].lineno == 2
        assert file_mutants[0].end_lineno == 2
        assert file_mutants[0].col_offset == 4
        assert file_mutants[0].end_col_offset == 15
        assert file_mutants[0].text == "return ''"


class TestDecoratorMutator:
    def test_mutator_name(self):
        assert DecoratorMutator.mutator_name == "Decorator"

    def test_decorator_mutator(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = DecoratorMutator(config=config, echo=mock_echo, other="value")
        module = "\n".join(  # noqa: FLY002
            [
                "@dec1",
                "@dec2",
                "@dec1",
                "def example(y):",
                "    return y",
            ],
        )
        file_mutants = mutator.create_mutations(ast.parse(module))

        assert len(file_mutants) == 3

        for mut in file_mutants:
            assert mut.lineno == 1
            assert mut.end_lineno == 5
            assert mut.col_offset == 1
            assert mut.end_col_offset == 12
