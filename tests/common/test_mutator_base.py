import ast
import importlib
from unittest import mock

import pytest

from poodle import mutate
from poodle.common import mutator_base


@pytest.fixture()
def _setup():
    importlib.reload(mutator_base)
    yield


class TestMutatorBase:
    def test_mutator_name(self):
        assert mutator_base.MutatorBase.mutator_name == ""

    @pytest.mark.parametrize(
        ("skip_mutators", "only_mutators", "expected"),
        [
            ([], [], True),
            (["other"], [], True),
            (["test"], [], False),
            ([], ["other"], False),
            ([], ["test"], True),
        ],
    )
    def test_is_enabled(self, skip_mutators, only_mutators, expected):
        mutator = mutator_base.MutatorBase()
        mutator.mutator_name = "Test"

        assert mutator.is_enabled(mock.MagicMock(skip_mutators=skip_mutators, only_mutators=only_mutators)) == expected

    def test_create_file_mutation(self):
        mutator = mutator_base.MutatorBase()
        mutator.mutator_name = "Test"

        node = mock.MagicMock(lineno=1, col_offset=2, end_lineno=3, end_col_offset=4)
        file_mutation = mutator.create_file_mutation(node, "changed text")

        assert file_mutation.mutator_name == "Test"
        assert file_mutation.lineno == 1
        assert file_mutation.col_offset == 2
        assert file_mutation.end_lineno == 3
        assert file_mutation.end_col_offset == 4
        assert file_mutation.text == "changed text"

    def test_get_location(self):
        module = "\n".join(  # noqa: FLY002
            [
                "@dec1",
                "def example(y):",
                "    return y",
            ],
        )
        assert mutator_base.MutatorBase().get_location(ast.parse(module).body[0]) == (1, 0, 3, 12)

    @mock.patch("ast.walk")
    def test_get_location_no_ends(self, walk):
        node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=None, end_col_offset=None)
        walk_nodes = [
            mock.MagicMock(lineno=4, col_offset=4),
            mock.MagicMock(lineno=3, col_offset=4),
        ]
        for m in walk_nodes:
            del m.end_lineno
            del m.end_col_offset
        walk.return_value = walk_nodes
        assert mutator_base.MutatorBase().get_location(node) == (3, 4, 5, 8)

    @mock.patch("ast.walk")
    def test_get_location_walk_no_location(self, walk):
        node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
        walk_nodes = [
            mock.MagicMock(),
        ]
        for m in walk_nodes:
            del m.lineno
            del m.col_offset
            del m.end_lineno
            del m.end_col_offset
        walk.return_value = walk_nodes
        assert mutator_base.MutatorBase().get_location(node) == (5, 8, 5, 12)

    @pytest.mark.parametrize(
        ("walk_return", "expected"),
        [
            (mock.MagicMock(lineno=4, col_offset=8, end_lineno=5, end_col_offset=8), (4, 8, 5, 12)),
            (mock.MagicMock(lineno=4, col_offset=9, end_lineno=5, end_col_offset=8), (4, 8, 5, 12)),
            (mock.MagicMock(lineno=4, col_offset=7, end_lineno=5, end_col_offset=8), (4, 7, 5, 12)),
            (mock.MagicMock(lineno=5, col_offset=1, end_lineno=5, end_col_offset=8), (5, 1, 5, 12)),
            (mock.MagicMock(lineno=5, col_offset=10, end_lineno=5, end_col_offset=8), (5, 8, 5, 12)),
            (mock.MagicMock(lineno=6, col_offset=1, end_lineno=6, end_col_offset=8), (5, 8, 6, 8)),
            (mock.MagicMock(lineno=5, col_offset=13, end_lineno=5, end_col_offset=15), (5, 8, 5, 15)),
            (mock.MagicMock(lineno=5, col_offset=13, end_lineno=5, end_col_offset=11), (5, 8, 5, 12)),
        ],
    )
    @mock.patch("ast.walk")
    def test_get_location_walk(self, walk, walk_return, expected):
        node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
        walk.return_value = [walk_return]
        assert mutator_base.MutatorBase().get_location(node) == expected

    def test_is_annotation_function_def(self):
        parsed_ast = ast.parse(
            "def my_func(xl: list[int] = 1)-> list[str]:\n  return [str(x) for x in xl]",
            mode="exec",
        )
        mutate.add_parent_attr(parsed_ast)

        assert not mutator_base.MutatorBase.is_annotation(parsed_ast)  ## no parent

        function_def = parsed_ast.body[0]
        arg_xl = function_def.args.args[0]
        arg_xl_annotation: ast.Subscript = arg_xl.annotation  # type: ignore [annotation-unchecked]
        arg_xl_default: ast.Constant = function_def.args.defaults[0]  # type: ignore [annotation-unchecked]

        assert mutator_base.MutatorBase.is_annotation(arg_xl_annotation) is True
        assert mutator_base.MutatorBase.is_annotation(arg_xl_annotation.value) is True  ## list
        assert mutator_base.MutatorBase.is_annotation(arg_xl_default) is False

        returns_subscript = function_def.returns
        assert mutator_base.MutatorBase.is_annotation(returns_subscript) is True
        assert mutator_base.MutatorBase.is_annotation(returns_subscript.value) is True  ## list

        list_comp = function_def.body[0].value
        assert mutator_base.MutatorBase.is_annotation(list_comp) is False

    def test_is_annotation_ann_assign(self):
        parsed_ast = ast.parse("x: list[str] | tuple[str] = y", mode="exec")
        mutate.add_parent_attr(parsed_ast)

        assert mutator_base.MutatorBase.is_annotation(parsed_ast) is False
        ann_assign = parsed_ast.body[0]
        assert mutator_base.MutatorBase.is_annotation(ann_assign) is False
        assert mutator_base.MutatorBase.is_annotation(ann_assign.target) is False  # Name: x
        assert mutator_base.MutatorBase.is_annotation(ann_assign.annotation) is True  # BinOp: BitOr
        assert mutator_base.MutatorBase.is_annotation(ann_assign.annotation.left) is True  # list[str]
        assert mutator_base.MutatorBase.is_annotation(ann_assign.annotation.left.value) is True  # list
        assert mutator_base.MutatorBase.is_annotation(ann_assign.value) is False  # Name: y

    def test_unparse_indent_lines_1(self):
        parsed_ast = ast.parse(
            "\n".join(["x = 1"]),
            mode="exec",
        )
        expected = "\n".join(["x = 1"])
        assert mutator_base.MutatorBase().unparse_indent(parsed_ast, 4) == expected

    def test_unparse_indent_lines_2(self):
        parsed_ast = ast.parse(
            "\n".join(
                [
                    "def my_func(xl: list[int] = 1)-> list[str]:",
                    "    return [str(x) for x in xl]",
                ]
            ),
            mode="exec",
        )
        expected = "\n".join(
            [
                "def my_func(xl: list[int]=1) -> list[str]:",
                "      return [str(x) for x in xl]",
            ]
        )
        assert mutator_base.MutatorBase().unparse_indent(parsed_ast, 2) == expected

    def test_unparse_indent_0(self):
        parsed_ast = ast.parse(
            "\n".join(
                [
                    "@staticmethod",
                    "def my_func(xl: list[int] = 1)-> list[str]:",
                    "    return [str(x) for x in xl]",
                ]
            ),
            mode="exec",
        )
        expected = "\n".join(
            [
                "@staticmethod",
                "def my_func(xl: list[int]=1) -> list[str]:",
                "    return [str(x) for x in xl]",
            ]
        )
        assert mutator_base.MutatorBase().unparse_indent(parsed_ast, 0) == expected

    def test_unparse_indent_4(self):
        parsed_ast = ast.parse(
            "\n".join(
                [
                    "class Example:",
                    "    @staticmethod",
                    "    def my_func(xl: list[int] = 1)-> list[str]:",
                    "        return [str(x) for x in xl]",
                ]
            ),
            mode="exec",
        )
        expected = "\n".join(
            [
                "@staticmethod",
                "    def my_func(xl: list[int]=1) -> list[str]:",
                "        return [str(x) for x in xl]",
            ]
        )
        assert mutator_base.MutatorBase().unparse_indent(parsed_ast.body[0].body[0], 4) == expected
