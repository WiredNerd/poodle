from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from unittest import mock

import pytest
from mock_decorator import MockDecorator

from poodle.common.config import PoodleConfigData
from poodle.common.data import FileMutation
from poodle.mutate import add_parent_attr
from poodle.mutators import mutator_subscript


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(mutator_subscript)
    yield
    importlib.reload(mutator_subscript)


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
    importlib.reload(mutator_subscript)
    mock_hook_impl_marker.assert_called_once_with("poodle")


class TestRegisterPlugins:
    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_subscript)
        mock_hookimpl.register_plugins.assert_called_once_with(specname="register_plugins")

    def test_register_plugins(self):
        plugin_manager = mock.MagicMock()
        with mock.patch("poodle.mutators.mutator_subscript.SubscriptMutator") as mock_bool_op_mutator:
            mutator_subscript.register_plugins(plugin_manager)
        plugin_manager.register.assert_called_once_with(mock_bool_op_mutator.return_value, "SubscriptMutator")


class TestSubscriptMutator:
    def test_vars(self):
        assert mutator_subscript.SubscriptMutator.mutator_name == "Subscript"

    def test_create_mutations(self):
        mutator = mutator_subscript.SubscriptMutator()
        parsed_ast = ast.parse("a = b[3]")
        config = PoodleConfigData()
        assert mutator.create_mutations(parsed_ast, config) == [
            FileMutation(
                mutator_name="Subscript",
                lineno=1,
                col_offset=4,
                end_lineno=1,
                end_col_offset=8,
                text="None",
            )
        ]

    def test_create_mutations_disabled(self):
        mutator = mutator_subscript.SubscriptMutator()
        parsed_ast = ast.parse("a = b[3]")
        config = PoodleConfigData()
        config.skip_mutators = ["Subscript".lower()]

        assert mutator.create_mutations(parsed_ast, config) == []

    def test_create_mutations_mock(self):
        mutator = mutator_subscript.SubscriptMutator()
        parsed_ast = ast.parse("a = b[3]")
        config = PoodleConfigData()
        with mock.patch.object(mutator, "visit") as mock_visit:
            assert mutator.create_mutations(parsed_ast, config) == mutator.mutants
        mock_visit.assert_called_once_with(parsed_ast)

    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_subscript)
        mock_hookimpl.create_mutations.assert_called_once_with(specname="create_mutations")

    @pytest.mark.parametrize(
        ("text_in", "text_out"),
        [
            ("a = b[3]", ["None"]),
            ("a = b['c']", ["None"]),
        ],
    )
    def test_visit_constant(self, text_in, text_out):
        mutator = mutator_subscript.SubscriptMutator()

        parsed_ast = ast.parse(text_in)
        add_parent_attr(parsed_ast)
        parsed_ast_copy = deepcopy(parsed_ast)
        config = PoodleConfigData()

        mutants = mutator.create_mutations(parsed_ast, config)

        assert mutants == [
            FileMutation(
                mutator_name="Subscript",
                lineno=1,
                col_offset=4,
                end_lineno=1,
                end_col_offset=len(text_in),
                text=must_text,
            )
            for must_text in text_out
        ]

        assert ast.dump(parsed_ast, include_attributes=True) == ast.dump(ast.parse(text_in), include_attributes=True)

        assert ast.dump(parsed_ast_copy, include_attributes=True) == ast.dump(parsed_ast, include_attributes=True)
