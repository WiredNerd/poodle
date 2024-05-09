from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from unittest import mock

import pytest
from mock_decorator import MockDecorator

from poodle.common.config import PoodleConfigData
from poodle.mutators import mutator_decorator


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(mutator_decorator)
    yield
    importlib.reload(mutator_decorator)


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
    importlib.reload(mutator_decorator)
    mock_hook_impl_marker.assert_called_once_with("poodle")


class TestRegisterPlugins:
    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_decorator)
        mock_hookimpl.register_plugins.assert_called_once_with(specname="register_plugins")

    def test_register_plugins(self):
        plugin_manager = mock.MagicMock()
        with mock.patch("poodle.mutators.mutator_decorator.DecoratorMutator") as mock_mutator_decorator:
            mutator_decorator.register_plugins(plugin_manager)
        plugin_manager.register.assert_called_once_with(mock_mutator_decorator.return_value, "DecoratorMutator")


class TestDecoratorMutator:
    def test_vars(self):
        assert mutator_decorator.DecoratorMutator.mutator_name == "Decorator"

    single_decorator = "\n".join(  # noqa: FLY002
        [
            "class Example:",
            "    @dec.abc",
            "    def example(y):",
            "        return y",
        ],
    )

    def test_create_mutations_single(self):
        mutator = mutator_decorator.DecoratorMutator()
        parsed_ast = ast.parse(self.single_decorator)
        parsed_ast_copy = deepcopy(parsed_ast)
        config = PoodleConfigData()
        file_mutants = mutator.create_mutations(parsed_ast, config)

        assert len(file_mutants) == 1

        for mut in file_mutants:
            assert mut.lineno == 2
            assert mut.end_lineno == 4
            assert mut.col_offset == 4
            assert mut.end_col_offset == 16

        assert file_mutants[0].text.splitlines() == [
            "def example(y):",
            "        return y",
        ]

        assert ast.dump(parsed_ast_copy, include_attributes=True) == ast.dump(parsed_ast, include_attributes=True)

    def test_create_mutations_disabled(self):
        mutator = mutator_decorator.DecoratorMutator()
        parsed_ast = ast.parse(self.single_decorator)
        config = PoodleConfigData()
        config.skip_mutators = ["Decorator".lower()]

        assert mutator.create_mutations(parsed_ast, config) == []

    multiple_decorators = "\n".join(  # noqa: FLY002
        [
            "@dec1",
            "@dec2(a)",
            "@dec1",
            "def example(y):",
            "    return y",
        ],
    )

    def test_decorator_mutator_multi(self):
        mutator = mutator_decorator.DecoratorMutator()
        parsed_ast = ast.parse(self.multiple_decorators)
        config = PoodleConfigData()
        file_mutants = mutator.create_mutations(parsed_ast, config)

        assert len(file_mutants) == 3

        for mut in file_mutants:
            assert mut.lineno == 1
            assert mut.end_lineno == 5
            assert mut.col_offset == 0
            assert mut.end_col_offset == 12

        assert file_mutants[0].text == "\n".join(  # noqa: FLY002
            [
                "@dec2(a)",
                "@dec1",
                "def example(y):",
                "    return y",
            ]
        )

        assert file_mutants[1].text == "\n".join(  # noqa: FLY002
            [
                "@dec1",
                "@dec1",
                "def example(y):",
                "    return y",
            ]
        )

        assert file_mutants[2].text == "\n".join(  # noqa: FLY002
            [
                "@dec1",
                "@dec2(a)",
                "def example(y):",
                "    return y",
            ]
        )
