from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from unittest import mock

import pytest
from mock_decorator import MockDecorator

from poodle.common.config import PoodleConfigData
from poodle.mutators import mutator_function_call


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(mutator_function_call)
    yield
    importlib.reload(mutator_function_call)


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
    importlib.reload(mutator_function_call)
    mock_hook_impl_marker.assert_called_once_with("poodle")


class TestRegisterPlugins:
    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_function_call)
        mock_hookimpl.register_plugins.assert_called_once_with(specname="register_plugins")

    def test_register_plugins(self):
        plugin_manager = mock.MagicMock()
        with mock.patch("poodle.mutators.mutator_function_call.FunctionCallMutator") as mock_mutator_function_call:
            mutator_function_call.register_plugins(plugin_manager)
        plugin_manager.register.assert_called_once_with(mock_mutator_function_call.return_value, "FunctionCallMutator")


class TestFunctionCallMutator:
    def test_vars(self):
        assert mutator_function_call.FunctionCallMutator.mutator_name == "FuncCall"

    def test_create_mutations(self):
        mutator = mutator_function_call.FunctionCallMutator()
        parsed_ast = ast.parse("y = ex_func(1)")
        parsed_ast_copy = deepcopy(parsed_ast)
        config = PoodleConfigData()
        file_mutants = mutator.create_mutations(parsed_ast, config)

        assert len(file_mutants) == 1

        for mut in file_mutants:
            assert mut.lineno == 1
            assert mut.end_lineno == 1
            assert mut.col_offset == 4
            assert mut.end_col_offset == 14
            assert mut.text == "None"

        assert ast.dump(parsed_ast_copy, include_attributes=True) == ast.dump(parsed_ast, include_attributes=True)

    def test_create_mutations_disabled(self):
        mutator = mutator_function_call.FunctionCallMutator()
        parsed_ast = ast.parse("y = ex_func(1)")
        config = PoodleConfigData()
        config.skip_mutators = ["FuncCall".lower()]

        assert mutator.create_mutations(parsed_ast, config) == []
