from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from unittest import mock

import pytest
from mock_decorator import MockDecorator

from poodle.common.config import PoodleConfigData
from poodle.common.data import FileMutation
from poodle.mutators import mutator_keyword


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(mutator_keyword)
    yield
    importlib.reload(mutator_keyword)


@pytest.fixture()
def mock_hook_impl_marker():
    with mock.patch("pluggy.HookimplMarker") as mock_hook_impl_marker:
        yield mock_hook_impl_marker


@pytest.fixture()
def mock_hookimpl(mock_hook_impl_marker):
    hookimpl = MockDecorator()
    mock_hook_impl_marker.return_value = hookimpl
    yield hookimpl


def test_hook_impl_marker(mock_hook_impl_marker):
    importlib.reload(mutator_keyword)
    mock_hook_impl_marker.assert_called_once_with("poodle")


class TestRegisterPlugins:
    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_keyword)
        mock_hookimpl.register_plugins.assert_called_once_with(specname="register_plugins")

    def test_register_plugins(self):
        plugin_manager = mock.MagicMock()
        with mock.patch("poodle.mutators.mutator_keyword.KeywordMutator") as mock_bool_op_mutator:
            mutator_keyword.register_plugins(plugin_manager)
        plugin_manager.register.assert_called_once_with(mock_bool_op_mutator.return_value, "KeywordMutator")


class TestKeywordMutator:
    def test_vars(self):
        assert mutator_keyword.KeywordMutator.mutator_name == "Keyword"

    def test_create_mutations(self):
        mutator = mutator_keyword.KeywordMutator()
        parsed_ast = ast.parse("True", mode="eval")
        config = PoodleConfigData()
        assert mutator.create_mutations(parsed_ast, config) == [
            FileMutation(
                mutator_name="Keyword",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=4,
                text="False",
            )
        ]

    def test_create_mutations_disabled(self):
        mutator = mutator_keyword.KeywordMutator()
        parsed_ast = ast.parse("True", mode="eval")
        config = PoodleConfigData()
        config.skip_mutators = ["Keyword".lower()]

        assert mutator.create_mutations(parsed_ast, config) == []

    def test_create_mutations_mock(self):
        mutator = mutator_keyword.KeywordMutator()
        parsed_ast = ast.parse("True", mode="eval")
        config = PoodleConfigData()
        with mock.patch.object(mutator, "visit") as mock_visit:
            assert mutator.create_mutations(parsed_ast, config) == mutator.mutants
        mock_visit.assert_called_once_with(parsed_ast)

    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_keyword)
        mock_hookimpl.create_mutations.assert_called_once_with(specname="create_mutations")

    @pytest.mark.parametrize(
        ("text_in", "text_out"),
        [
            ("True", ["False"]),
            ("False", ["True"]),
            ("None", ["' '"]),
        ],
    )
    def test_visit_bool_op(self, text_in, text_out):
        mutator = mutator_keyword.KeywordMutator()

        parsed_ast = ast.parse(text_in, mode="eval")
        parsed_ast_copy = deepcopy(parsed_ast)
        config = PoodleConfigData()

        mutants = mutator.create_mutations(parsed_ast, config)

        assert mutants == [
            FileMutation(
                mutator_name="Keyword",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=len(text_in),
                text=must_text,
            )
            for must_text in text_out
        ]

        assert ast.dump(parsed_ast, include_attributes=True) == ast.dump(
            ast.parse(text_in, mode="eval"), include_attributes=True
        )

        assert ast.dump(parsed_ast_copy, include_attributes=True) == ast.dump(parsed_ast, include_attributes=True)

    def test_visit_constant_is_annotation(self):
        mutator = mutator_keyword.KeywordMutator()
        parsed_ast = ast.parse("a: int | None = 1")
        config = PoodleConfigData()

        mutator.is_annotation = mock.MagicMock(return_value=True)

        assert mutator.create_mutations(parsed_ast, config) == []

    def test_visit_constant_no_mapping(self):
        mutator = mutator_keyword.KeywordMutator()
        parsed_ast = ast.parse("continue")
        config = PoodleConfigData()

        assert mutator.create_mutations(parsed_ast, config) == []
