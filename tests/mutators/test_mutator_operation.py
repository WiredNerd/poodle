from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from unittest import mock

import pytest
from mock_decorator import MockDecorator

from poodle.common.config import PoodleConfigData
from poodle.common.data import FileMutation
from poodle.mutators import mutator_operation


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(mutator_operation)
    yield
    importlib.reload(mutator_operation)


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
    importlib.reload(mutator_operation)
    mock_hook_impl_marker.assert_called_once_with("poodle")


class TestRegisterPlugins:
    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_operation)
        mock_hookimpl.register_plugins.assert_called_once_with(specname="register_plugins")

    def test_register_plugins(self):
        plugin_manager = mock.MagicMock()
        with (
            mock.patch("poodle.mutators.mutator_operation.BinaryOperationMutator") as mock_bin_op_mutator,
            mock.patch("poodle.mutators.mutator_operation.AugAssignMutator") as mock_aug_assign_mutator,
        ):
            mutator_operation.register_plugins(plugin_manager)
        plugin_manager.register.assert_has_calls(
            [
                mock.call(mock_bin_op_mutator.return_value, "BinaryOperationMutator"),
                mock.call(mock_aug_assign_mutator.return_value, "AugAssignMutator"),
            ]
        )


class TestOperationMutator:
    def test_register_plugins_hookimpl(self, mock_hookimpl):
        importlib.reload(mutator_operation)
        mock_hookimpl.configure.assert_called_once_with(specname="configure")
        mock_hookimpl.create_mutations.assert_called_once_with(specname="create_mutations")

    @pytest.mark.parametrize(
        ("mutator_opts", "expected_level"),
        [
            ({}, "std"),
            ({"operator_level": "min"}, "min"),
            ({"operator_level": "MIN"}, "min"),
            ({"operator_level": "std"}, "std"),
            ({"operator_level": "STD"}, "std"),
            ({"operator_level": "max"}, "max"),
            ({"operator_level": "MAX"}, "max"),
        ],
    )
    def test_configure(self, mutator_opts: dict, expected_level: str):
        mutator = mutator_operation.OperationMutator()
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = mutator_opts
        secho = mock.MagicMock()
        mutator.configure(config, secho)
        assert mutator.type_map == mutator.type_map_levels[expected_level]
        secho.assert_not_called()

    def test_configure_invalid(self):
        mutator = mutator_operation.OperationMutator()
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": "invalid"}
        secho = mock.MagicMock()
        mutator.configure(config, secho)
        assert mutator.type_map == mutator.type_map_levels["std"]
        secho.assert_called_once_with(
            "WARN: Invalid value operator_opts.operator_level=invalid.  Using Default value 'std'", fg="yellow"
        )


class TestBinaryOperationMutator:
    def test_vars(self):
        assert mutator_operation.BinaryOperationMutator.mutator_name == "BinOp"

    def test_create_mutations(self):
        mutator = mutator_operation.BinaryOperationMutator()
        parsed_ast = ast.parse("1 + 1")
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": "min"}
        config.skip_mutators = []
        config.only_mutators = []
        mutator.configure(config, mock.MagicMock())
        assert mutator.create_mutations(parsed_ast, config) == [
            FileMutation(
                mutator_name="BinOp",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=5,
                text="1 * 1",
            )
        ]

    def test_create_mutations_disabled(self):
        mutator = mutator_operation.BinaryOperationMutator()
        parsed_ast = ast.parse("1 + 1")
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": "min"}
        config.skip_mutators = ["BinOp".lower()]

        assert mutator.create_mutations(parsed_ast, config) == []

    def test_create_mutations_mock(self):
        mutator = mutator_operation.BinaryOperationMutator()
        parsed_ast = ast.parse("1 + 1")
        config = PoodleConfigData()
        with mock.patch.object(mutator, "visit") as mock_visit:
            assert mutator.create_mutations(parsed_ast, config) == mutator.mutants
        mock_visit.assert_called_once_with(parsed_ast)

    @pytest.mark.parametrize(
        ("level", "text_in", "text_out"),
        [
            ("min", "1 + 2", ["1 * 2"]),
            ("min", "1 - 2", ["1 / 2"]),
            ("min", "1 * 2", ["1 + 2"]),
            ("min", "1 / 2", ["1 - 2"]),
            ("min", "1 // 2", ["1 / 2"]),
            ("min", "1 % 2", ["1 - 2"]),
            ("min", "1 ** 2", ["1 * 2"]),
            ("min", "1 >> 2", ["1 << 2"]),
            ("min", "1 << 2", ["1 >> 2"]),
            ("min", "1 | 2", ["1 & 2"]),
            ("min", "1 ^ 2", ["1 | 2"]),
            ("min", "1 & 2", ["1 ^ 2"]),
            ("min", "1 @ 2", []),
            ("std", "1 + 2", ["1 - 2", "1 * 2"]),
            ("std", "1 - 2", ["1 + 2", "1 / 2"]),
            ("std", "1 * 2", ["1 / 2", "1 + 2"]),
            ("std", "1 / 2", ["1 * 2", "1 - 2"]),
            ("std", "1 // 2", ["1 * 2", "1 / 2"]),
            ("std", "1 % 2", ["1 // 2", "1 - 2"]),
            ("std", "1 ** 2", ["1 * 2", "1 / 2"]),
            ("std", "1 >> 2", ["1 << 2"]),
            ("std", "1 << 2", ["1 >> 2"]),
            ("std", "1 | 2", ["1 & 2"]),
            ("std", "1 ^ 2", ["1 | 2", "1 & 2"]),
            ("std", "1 & 2", ["1 | 2", "1 ^ 2"]),
            ("std", "1 @ 2", []),
            ("max", "1 + 2", ["1 - 2", "1 * 2", "1 / 2", "1 // 2", "1 % 2", "1 ** 2"]),
            ("max", "1 - 2", ["1 + 2", "1 * 2", "1 / 2", "1 // 2", "1 % 2", "1 ** 2"]),
            ("max", "1 * 2", ["1 + 2", "1 - 2", "1 / 2", "1 // 2", "1 % 2", "1 ** 2"]),
            ("max", "1 / 2", ["1 + 2", "1 - 2", "1 * 2", "1 // 2", "1 % 2", "1 ** 2"]),
            ("max", "1 // 2", ["1 + 2", "1 - 2", "1 * 2", "1 / 2", "1 % 2", "1 ** 2"]),
            ("max", "1 % 2", ["1 + 2", "1 - 2", "1 * 2", "1 / 2", "1 // 2", "1 ** 2"]),
            ("max", "1 ** 2", ["1 + 2", "1 - 2", "1 * 2", "1 / 2", "1 // 2", "1 % 2"]),
            ("max", "1 >> 2", ["1 << 2", "1 | 2", "1 ^ 2", "1 & 2"]),
            ("max", "1 << 2", ["1 >> 2", "1 | 2", "1 ^ 2", "1 & 2"]),
            ("max", "1 | 2", ["1 << 2", "1 >> 2", "1 ^ 2", "1 & 2"]),
            ("max", "1 ^ 2", ["1 << 2", "1 >> 2", "1 | 2", "1 & 2"]),
            ("max", "1 & 2", ["1 << 2", "1 >> 2", "1 | 2", "1 ^ 2"]),
            ("max", "1 @ 2", []),
        ],
    )
    def test_visit_bool_op(self, level, text_in, text_out):
        mutator = mutator_operation.BinaryOperationMutator()

        parsed_ast = ast.parse(text_in)
        parsed_ast_copy = deepcopy(parsed_ast)
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": level}
        config.skip_mutators = []
        config.only_mutators = []
        mutator.configure(config, mock.MagicMock())
        mutants = mutator.create_mutations(parsed_ast, config)

        assert mutants == [
            FileMutation(
                mutator_name="BinOp",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=len(text_in),
                text=must_text,
            )
            for must_text in text_out
        ]

        assert ast.dump(parsed_ast, include_attributes=True) == ast.dump(ast.parse(text_in), include_attributes=True)

        assert ast.dump(parsed_ast_copy, include_attributes=True) == ast.dump(parsed_ast, include_attributes=True)

    def test_visit_bool_op_annotation(self):
        mutator = mutator_operation.BinaryOperationMutator()

        parsed_ast = ast.parse("\n".join(["a: int | None = 1"]))
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": "std"}
        config.skip_mutators = []
        config.only_mutators = []
        mutator.configure(config, mock.MagicMock())
        mutator.is_annotation = mock.MagicMock(return_value=True)
        assert mutator.create_mutations(parsed_ast, config) == []


class TestAugAssignMutator:
    def test_vars(self):
        assert mutator_operation.AugAssignMutator.mutator_name == "AugAssign"

    def test_create_mutations(self):
        mutator = mutator_operation.AugAssignMutator()
        parsed_ast = ast.parse("a += 1")
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": "min"}
        config.skip_mutators = []
        config.only_mutators = []
        mutator.configure(config, mock.MagicMock())
        assert mutator.create_mutations(parsed_ast, config) == [
            FileMutation(
                mutator_name="AugAssign",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=6,
                text="a = 1",
            ),
            FileMutation(
                mutator_name="AugAssign",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=6,
                text="a *= 1",
            ),
        ]

    def test_create_mutations_disabled(self):
        mutator = mutator_operation.AugAssignMutator()
        parsed_ast = ast.parse("a += 1")
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": "min"}
        config.skip_mutators = ["AugAssign".lower()]

        assert mutator.create_mutations(parsed_ast, config) == []

    def test_create_mutations_mock(self):
        mutator = mutator_operation.AugAssignMutator()
        parsed_ast = ast.parse("a += 1")
        config = PoodleConfigData()
        with mock.patch.object(mutator, "visit") as mock_visit:
            assert mutator.create_mutations(parsed_ast, config) == mutator.mutants
        mock_visit.assert_called_once_with(parsed_ast)

    @pytest.mark.parametrize(
        ("level", "text_in", "text_out"),
        [
            ("min", "a += 2", ["a = 2", "a *= 2"]),
            ("min", "a -= 2", ["a = 2", "a /= 2"]),
            ("min", "a *= 2", ["a = 2", "a += 2"]),
            ("min", "a /= 2", ["a = 2", "a -= 2"]),
            ("min", "a //= 2", ["a = 2", "a /= 2"]),
            ("min", "a %= 2", ["a = 2", "a -= 2"]),
            ("min", "a **= 2", ["a = 2", "a *= 2"]),
            ("min", "a >>= 2", ["a = 2", "a <<= 2"]),
            ("min", "a <<= 2", ["a = 2", "a >>= 2"]),
            ("min", "a |= 2", ["a = 2", "a &= 2"]),
            ("min", "a ^= 2", ["a = 2", "a |= 2"]),
            ("min", "a &= 2", ["a = 2", "a ^= 2"]),
            ("min", "a @= 2", ["a = 2"]),
            ("std", "a += 2", ["a = 2", "a -= 2", "a *= 2"]),
            ("std", "a -= 2", ["a = 2", "a += 2", "a /= 2"]),
            ("std", "a *= 2", ["a = 2", "a /= 2", "a += 2"]),
            ("std", "a /= 2", ["a = 2", "a *= 2", "a -= 2"]),
            ("std", "a //= 2", ["a = 2", "a *= 2", "a /= 2"]),
            ("std", "a %= 2", ["a = 2", "a //= 2", "a -= 2"]),
            ("std", "a **= 2", ["a = 2", "a *= 2", "a /= 2"]),
            ("std", "a >>= 2", ["a = 2", "a <<= 2"]),
            ("std", "a <<= 2", ["a = 2", "a >>= 2"]),
            ("std", "a |= 2", ["a = 2", "a &= 2"]),
            ("std", "a ^= 2", ["a = 2", "a |= 2", "a &= 2"]),
            ("std", "a &= 2", ["a = 2", "a |= 2", "a ^= 2"]),
            ("std", "a @= 2", ["a = 2"]),
            ("max", "a += 2", ["a = 2", "a -= 2", "a *= 2", "a /= 2", "a //= 2", "a %= 2", "a **= 2"]),
            ("max", "a -= 2", ["a = 2", "a += 2", "a *= 2", "a /= 2", "a //= 2", "a %= 2", "a **= 2"]),
            ("max", "a *= 2", ["a = 2", "a += 2", "a -= 2", "a /= 2", "a //= 2", "a %= 2", "a **= 2"]),
            ("max", "a /= 2", ["a = 2", "a += 2", "a -= 2", "a *= 2", "a //= 2", "a %= 2", "a **= 2"]),
            ("max", "a //= 2", ["a = 2", "a += 2", "a -= 2", "a *= 2", "a /= 2", "a %= 2", "a **= 2"]),
            ("max", "a %= 2", ["a = 2", "a += 2", "a -= 2", "a *= 2", "a /= 2", "a //= 2", "a **= 2"]),
            ("max", "a **= 2", ["a = 2", "a += 2", "a -= 2", "a *= 2", "a /= 2", "a //= 2", "a %= 2"]),
            ("max", "a >>= 2", ["a = 2", "a <<= 2", "a |= 2", "a ^= 2", "a &= 2"]),
            ("max", "a <<= 2", ["a = 2", "a >>= 2", "a |= 2", "a ^= 2", "a &= 2"]),
            ("max", "a |= 2", ["a = 2", "a <<= 2", "a >>= 2", "a ^= 2", "a &= 2"]),
            ("max", "a ^= 2", ["a = 2", "a <<= 2", "a >>= 2", "a |= 2", "a &= 2"]),
            ("max", "a &= 2", ["a = 2", "a <<= 2", "a >>= 2", "a |= 2", "a ^= 2"]),
            ("max", "a @= 2", ["a = 2"]),
        ],
    )
    def test_visit_aug_assign(self, level, text_in, text_out):
        mutator = mutator_operation.AugAssignMutator()

        parsed_ast = ast.parse(text_in)
        parsed_ast_copy = deepcopy(parsed_ast)
        config = mock.MagicMock()
        config.merge_dict_from_config.return_value = {"operator_level": level}
        config.skip_mutators = []
        config.only_mutators = []
        mutator.configure(config, mock.MagicMock())
        mutants = mutator.create_mutations(parsed_ast, config)

        assert mutants == [
            FileMutation(
                mutator_name="AugAssign",
                lineno=1,
                col_offset=0,
                end_lineno=1,
                end_col_offset=len(text_in),
                text=must_text,
            )
            for must_text in text_out
        ]

        assert ast.dump(parsed_ast, include_attributes=True) == ast.dump(ast.parse(text_in), include_attributes=True)

        assert ast.dump(parsed_ast_copy, include_attributes=True) == ast.dump(parsed_ast, include_attributes=True)
