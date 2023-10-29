import ast
from unittest import mock

import pytest

from poodle.data import FileMutant, PoodleConfig
from poodle.mutators import BinaryOperationMutator, PoodleMutator


@pytest.fixture()
def mock_print():
    with mock.patch("builtins.print") as mock_print:
        yield mock_print


class TestPoodleMutator:
    class PoodleMutatorTest(PoodleMutator):
        def create_mutants(self, parsed_ast: ast.Module) -> list[FileMutant]:
            return []

    def test_abstract(self):
        with pytest.raises(TypeError, match="^Can't instantiate abstract class.*create_mutants.*"):
            PoodleMutator(config=mock.MagicMock(spec=PoodleConfig))

    def test_init(self):
        config = mock.MagicMock(spec=PoodleConfig)
        mutator = self.PoodleMutatorTest(config=config)

        assert mutator.config == config


example_file = """
def ex_func(x, y):
    return x + y

def subtraction(x, z):
    return x - z
"""


class TestBinaryOperationMutator:
    def test_init_default(self, mock_print):
        config = mock.MagicMock(mutator_opts={})
        mutator = BinaryOperationMutator(config)
        assert mutator.config == config
        assert mutator.file_mutants == []
        assert mutator.type_map == mutator.type_map_levels[2]
        mock_print.assert_not_called()

    def test_init_1(self, mock_print):
        config = mock.MagicMock(mutator_opts={"bin_op_level": 1})
        mutator = BinaryOperationMutator(config)
        assert mutator.config == config
        assert mutator.file_mutants == []
        assert mutator.type_map == mutator.type_map_levels[1]
        mock_print.assert_not_called()

    def test_init_2(self, mock_print):
        config = mock.MagicMock(mutator_opts={"bin_op_level": "2"})
        mutator = BinaryOperationMutator(config)
        assert mutator.config == config
        assert mutator.file_mutants == []
        assert mutator.type_map == mutator.type_map_levels[2]
        mock_print.assert_not_called()

    def test_init_3(self, mock_print):
        config = mock.MagicMock(mutator_opts={"bin_op_level": "3"})
        mutator = BinaryOperationMutator(config)
        assert mutator.config == config
        assert mutator.file_mutants == []
        assert mutator.type_map == mutator.type_map_levels[3]
        mock_print.assert_not_called()

    def test_init_4(self, mock_print):
        config = mock.MagicMock(mutator_opts={"bin_op_level": "4"})
        mutator = BinaryOperationMutator(config)
        assert mutator.config == config
        assert mutator.file_mutants == []
        assert mutator.type_map == mutator.type_map_levels[2]
        mock_print.assert_called_with("WARN: Invalid value operator_opts.bin_op_level=4.  Using Default value 2.")

    def test_create_mutants(self):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={}))

        file_mutants = mutator.create_mutants(ast.parse(example_file))

        assert len(file_mutants) == 4

        file_mutant = file_mutants[0]
        assert file_mutant.lineno == 3
        assert file_mutant.text == "x - y"

        file_mutant = file_mutants[1]
        assert file_mutant.lineno == 3
        assert file_mutant.text == "x * y"

        file_mutant = file_mutants[2]
        assert file_mutant.lineno == 6
        assert file_mutant.text == "x + z"

        file_mutant = file_mutants[3]
        assert file_mutant.lineno == 6
        assert file_mutant.text == "x / z"

    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["1 - 2"]),
            (ast.Sub, ["1 + 2"]),
            (ast.Mult, ["1 / 2"]),
            (ast.Div, ["1 * 2"]),
            (ast.FloorDiv, ["1 / 2"]),
            (ast.Mod, ["1 // 2"]),
            (ast.Pow, ["1 * 2"]),
            (ast.RShift, ["1 << 2"]),
            (ast.LShift, ["1 >> 2"]),
            (ast.BitOr, ["1 & 2"]),
            (ast.BitXor, ["1 | 2"]),
            (ast.BitAnd, ["1 ^ 2"]),
            (ast.MatMult, []),
        ],
    )
    def test_visit_BinOp_level_1(self, op_type, text_out):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={"bin_op_level": 1}))

        node = ast.BinOp()
        node.left = ast.Constant()
        node.left.value = 1
        node.op = op_type()
        node.right = ast.Constant()
        node.right.value = 2

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_BinOp(node)

        assert [file_mutant.text for file_mutant in mutator.file_mutants] == text_out

    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["1 - 2", "1 * 2"]),
            (ast.Sub, ["1 + 2", "1 / 2"]),
            (ast.Mult, ["1 / 2", "1 + 2"]),
            (ast.Div, ["1 * 2", "1 - 2"]),
            (ast.FloorDiv, ["1 / 2"]),
            (ast.Mod, ["1 // 2"]),
            (ast.Pow, ["1 * 2"]),
            (ast.RShift, ["1 << 2"]),
            (ast.LShift, ["1 >> 2"]),
            (ast.BitOr, ["1 & 2", "1 ^ 2"]),
            (ast.BitXor, ["1 | 2", "1 & 2"]),
            (ast.BitAnd, ["1 ^ 2", "1 | 2"]),
            (ast.MatMult, []),
        ],
    )
    def test_visit_BinOp_level_2(self, op_type, text_out):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={"bin_op_level": 2}))

        node = ast.BinOp()
        node.left = ast.Constant()
        node.left.value = 1
        node.op = op_type()
        node.right = ast.Constant()
        node.right.value = 2

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_BinOp(node)

        assert [file_mutant.text for file_mutant in mutator.file_mutants] == text_out

    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["1 - 2", "1 * 2", "1 / 2", "1 // 2", "1 % 2", "1 ** 2"]),
            (ast.Sub, ["1 + 2", "1 * 2", "1 / 2", "1 // 2", "1 % 2", "1 ** 2"]),
            (ast.Mult, ["1 + 2", "1 - 2", "1 / 2", "1 // 2", "1 % 2", "1 ** 2"]),
            (ast.Div, ["1 + 2", "1 - 2", "1 * 2", "1 // 2", "1 % 2", "1 ** 2"]),
            (ast.FloorDiv, ["1 + 2", "1 - 2", "1 * 2", "1 / 2", "1 % 2", "1 ** 2"]),
            (ast.Mod, ["1 + 2", "1 - 2", "1 * 2", "1 / 2", "1 // 2", "1 ** 2"]),
            (ast.Pow, ["1 + 2", "1 - 2", "1 * 2", "1 / 2", "1 // 2", "1 % 2"]),
            (ast.RShift, ["1 << 2", "1 | 2", "1 ^ 2", "1 & 2"]),
            (ast.LShift, ["1 >> 2", "1 | 2", "1 ^ 2", "1 & 2"]),
            (ast.BitOr, ["1 << 2", "1 >> 2", "1 ^ 2", "1 & 2"]),
            (ast.BitXor, ["1 << 2", "1 >> 2", "1 | 2", "1 & 2"]),
            (ast.BitAnd, ["1 << 2", "1 >> 2", "1 | 2", "1 ^ 2"]),
            (ast.MatMult, []),
        ],
    )
    def test_visit_BinOp_level_3(self, op_type, text_out):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={"bin_op_level": 3}))

        node = ast.BinOp()
        node.left = ast.Constant()
        node.left.value = 1
        node.op = op_type()
        node.right = ast.Constant()
        node.right.value = 2

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_BinOp(node)

        assert [file_mutant.text for file_mutant in mutator.file_mutants] == text_out

    def test_create_file_mutant(self):
        node = ast.BinOp()
        node.left = ast.Constant()
        node.left.value = 1
        node.op = ast.Add()
        node.right = ast.Constant()
        node.right.value = 2

        node.lineno = 20
        node.col_offset = 4
        node.end_lineno = 21
        node.end_col_offset = 10

        new_type = ast.Sub

        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={}))
        fm = mutator.create_file_mutant(node, new_type)

        assert fm.lineno == 20
        assert fm.col_offset == 4
        assert fm.end_lineno == 21
        assert fm.end_col_offset == 10
        assert fm.text == "1 - 2"
