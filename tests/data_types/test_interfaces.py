# import ast
# from unittest import mock

# import click
# import pytest

# from poodle.common.data import FileMutation, PoodleConfig
# from poodle.common.interfaces import Mutator, create_mutations, reporter, runner


# def test_create_mutations():
#     assert create_mutations(config=None, echo=None, parsed_ast=None, other=None, file_lines=None) is None


# class TestMutator:
#     class DummyMutator(Mutator):
#         mutator_name = "DummyMutator"

#         def create_mutations(self, *_, **__) -> list[FileMutation]:  # type: ignore [override]
#             return []

#     def test_abstract(self):
#         with pytest.raises(TypeError, match="^Can't instantiate abstract class.*create_mutations*"):
#             Mutator(config=mock.MagicMock(spec=PoodleConfig))

#     def test_init(self):
#         config = mock.MagicMock(spec=PoodleConfig)
#         mutator = self.DummyMutator(config=config, echo=click.echo, other="value")

#         assert mutator.config == config
#         assert mutator.echo == click.echo

#     def test_mutator_name(self):
#         assert Mutator.mutator_name == ""
#         assert self.DummyMutator.mutator_name == "DummyMutator"

#     def test_create_file_mutation(self):
#         node = mock.MagicMock(lineno=1, col_offset=2, end_lineno=3, end_col_offset=4)
#         file_mutation = self.DummyMutator.create_file_mutation(node, "changed text")

#         assert file_mutation.mutator_name == "DummyMutator"
#         assert file_mutation.lineno == 1
#         assert file_mutation.col_offset == 2
#         assert file_mutation.end_lineno == 3
#         assert file_mutation.end_col_offset == 4
#         assert file_mutation.text == "changed text"

#     def test_get_location(self):
#         module = "\n".join(  # noqa: FLY002
#             [
#                 "@dec1",
#                 "def example(y):",
#                 "    return y",
#             ],
#         )

#         assert Mutator.get_location(ast.parse(module).body[0]) == (1, 0, 3, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_no_ends(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=None, end_col_offset=None)
#         walk_nodes = [
#             mock.MagicMock(lineno=4, col_offset=4),
#             mock.MagicMock(lineno=3, col_offset=4),
#         ]
#         for m in walk_nodes:
#             del m.end_lineno
#             del m.end_col_offset
#         walk.return_value = walk_nodes
#         assert Mutator.get_location(node) == (3, 4, 5, 8)

#     @mock.patch("ast.walk")
#     def test_get_location_walk_no_location(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk_nodes = [
#             mock.MagicMock(),
#         ]
#         for m in walk_nodes:
#             del m.lineno
#             del m.col_offset
#             del m.end_lineno
#             del m.end_col_offset
#         walk.return_value = walk_nodes
#         assert Mutator.get_location(node) == (5, 8, 5, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_lt_lineno_eq_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=4, col_offset=8, end_lineno=5, end_col_offset=8),
#         ]
#         assert Mutator.get_location(node) == (4, 8, 5, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_lt_lineno_gt_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=4, col_offset=9, end_lineno=5, end_col_offset=8),
#         ]
#         assert Mutator.get_location(node) == (4, 8, 5, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_lt_lineno_lt_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=4, col_offset=7, end_lineno=5, end_col_offset=8),
#         ]
#         assert Mutator.get_location(node) == (4, 7, 5, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_eq_lineno_lt_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=5, col_offset=1, end_lineno=5, end_col_offset=8),
#         ]
#         assert Mutator.get_location(node) == (5, 1, 5, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_eq_lineno_gt_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=5, col_offset=10, end_lineno=5, end_col_offset=8),
#         ]
#         assert Mutator.get_location(node) == (5, 8, 5, 12)

#     @mock.patch("ast.walk")
#     def test_get_location_gt_end_lineno_lt_end_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=6, col_offset=1, end_lineno=6, end_col_offset=8),
#         ]
#         assert Mutator.get_location(node) == (5, 8, 6, 8)

#     @mock.patch("ast.walk")
#     def test_get_location_eq_end_lineno_gt_end_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=5, col_offset=13, end_lineno=5, end_col_offset=15),
#         ]
#         assert Mutator.get_location(node) == (5, 8, 5, 15)

#     @mock.patch("ast.walk")
#     def test_get_location_eq_end_lineno_lt_end_col(self, walk):
#         node = mock.MagicMock(lineno=5, col_offset=8, end_lineno=5, end_col_offset=12)
#         walk.return_value = [
#             mock.MagicMock(lineno=5, col_offset=13, end_lineno=5, end_col_offset=11),
#         ]
#         assert Mutator.get_location(node) == (5, 8, 5, 12)

#     def test_add_parent_attr(self):
#         parsed_ast = ast.parse("x+1", mode="eval")
#         Mutator.add_parent_attr(parsed_ast)

#         bin_op = parsed_ast.body

#         assert bin_op.parent == parsed_ast
#         assert bin_op.left.parent == bin_op
#         assert bin_op.op.parent == bin_op
#         assert bin_op.right.parent == bin_op

#     def test_is_annotation_function_def(self):
#         parsed_ast = ast.parse(
#             "def my_func(xl: list[int] = 1)-> list[str]:\n  return [str(x) for x in xl]",
#             mode="exec",
#         )
#         Mutator.add_parent_attr(parsed_ast)

#         assert not Mutator.is_annotation(parsed_ast)  ## no parent

#         function_def = parsed_ast.body[0]
#         arg_xl = function_def.args.args[0]
#         arg_xl_annotation: ast.Subscript = arg_xl.annotation  # type: ignore [annotation-unchecked]
#         arg_xl_default: ast.Constant = function_def.args.defaults[0]  # type: ignore [annotation-unchecked]

#         assert Mutator.is_annotation(arg_xl_annotation) is True
#         assert Mutator.is_annotation(arg_xl_annotation.value) is True  ## list
#         assert Mutator.is_annotation(arg_xl_default) is False

#         returns_subscript = function_def.returns
#         assert Mutator.is_annotation(returns_subscript) is True
#         assert Mutator.is_annotation(returns_subscript.value) is True  ## list

#         list_comp = function_def.body[0].value
#         assert Mutator.is_annotation(list_comp) is False

#     def test_is_annotation_ann_assign(self):
#         parsed_ast = ast.parse("x: list[str] | tuple[str] = y", mode="exec")
#         Mutator.add_parent_attr(parsed_ast)

#         assert Mutator.is_annotation(parsed_ast) is False
#         ann_assign = parsed_ast.body[0]
#         assert Mutator.is_annotation(ann_assign) is False
#         assert Mutator.is_annotation(ann_assign.target) is False  # Name: x
#         assert Mutator.is_annotation(ann_assign.annotation) is True  # BinOp: BitOr
#         assert Mutator.is_annotation(ann_assign.annotation.left) is True  # list[str]
#         assert Mutator.is_annotation(ann_assign.annotation.left.value) is True  # list
#         assert Mutator.is_annotation(ann_assign.value) is False  # Name: y


# def test_runner():
#     assert runner(config=None, echo=None, run_folder=None, mutant=None, timeout=None, other="value") is None


# def test_reporter():
#     assert reporter(config=None, echo=None, testing_results=None, other="value") is None
