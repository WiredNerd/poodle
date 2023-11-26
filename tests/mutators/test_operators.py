import ast
from unittest import mock

import pytest

from poodle.mutators.operators import AugAssignMutator, BinaryOperationMutator, OperationMutator


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


example_file = """
def ex_func(x, y):
    return x + y

def subtraction(x, z):
    return x - z
"""


class TestOperationMutator:
    def test_init_default(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = OperationMutator(config=config, echo=mock_echo, other="value")
        assert mutator.config == config
        assert mutator.mutants == []
        assert mutator.type_map == mutator.type_map_levels["std"]
        mock_echo.assert_not_called()

    def test_init_valid_level(self, mock_echo):
        config = mock.MagicMock(mutator_opts={"operator_level": "min"})
        mutator = OperationMutator(config, mock_echo)
        assert mutator.config == config
        assert mutator.mutants == []
        assert mutator.type_map == mutator.type_map_levels["min"]
        mock_echo.assert_not_called()

    def test_init_invalid_level(self, mock_echo):
        config = mock.MagicMock(mutator_opts={"operator_level": "super"})
        mutator = OperationMutator(config, mock_echo)
        assert mutator.config == config
        assert mutator.mutants == []
        assert mutator.type_map == mutator.type_map_levels["std"]
        mock_echo.assert_called_with(
            "WARN: Invalid value operator_opts.operator_level=super.  Using Default value 'std'",
        )

    def test_create_mutations(self, mock_echo):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={}), mock_echo)

        file_mutants = mutator.create_mutations(ast.parse(example_file))

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


class TestBinaryOperationMutator:
    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["1 * 2"]),
            (ast.Sub, ["1 / 2"]),
            (ast.Mult, ["1 + 2"]),
            (ast.Div, ["1 - 2"]),
            (ast.FloorDiv, ["1 / 2"]),
            (ast.Mod, ["1 - 2"]),
            (ast.Pow, ["1 * 2"]),
            (ast.RShift, ["1 << 2"]),
            (ast.LShift, ["1 >> 2"]),
            (ast.BitOr, ["1 & 2"]),
            (ast.BitXor, ["1 | 2"]),
            (ast.BitAnd, ["1 ^ 2"]),
            (ast.MatMult, []),
        ],
    )
    def test_visit_BinOp_level_min(self, op_type, text_out, mock_echo):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={"operator_level": "min"}), mock_echo)

        node = ast.BinOp()
        node.left = ast.Constant(1)
        node.op = op_type()
        node.right = ast.Constant(2)

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_BinOp(node)

        assert [file_mutant.text for file_mutant in mutator.mutants] == text_out

    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["1 - 2", "1 * 2"]),
            (ast.Sub, ["1 + 2", "1 / 2"]),
            (ast.Mult, ["1 / 2", "1 + 2"]),
            (ast.Div, ["1 * 2", "1 - 2"]),
            (ast.FloorDiv, ["1 * 2", "1 / 2"]),
            (ast.Mod, ["1 // 2", "1 - 2"]),
            (ast.Pow, ["1 * 2", "1 / 2"]),
            (ast.RShift, ["1 << 2"]),
            (ast.LShift, ["1 >> 2"]),
            (ast.BitOr, ["1 & 2", "1 ^ 2"]),
            (ast.BitXor, ["1 | 2", "1 & 2"]),
            (ast.BitAnd, ["1 ^ 2", "1 | 2"]),
            (ast.MatMult, []),
        ],
    )
    def test_visit_BinOp_level_std(self, op_type, text_out, mock_echo):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={"operator_level": "std"}), mock_echo)

        node = ast.BinOp()
        node.left = ast.Constant(1)
        node.op = op_type()
        node.right = ast.Constant(2)

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_BinOp(node)

        assert [file_mutant.text for file_mutant in mutator.mutants] == text_out

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
    def test_visit_BinOp_level_max(self, op_type, text_out, mock_echo):
        mutator = BinaryOperationMutator(mock.MagicMock(mutator_opts={"operator_level": "max"}), mock_echo)

        node = ast.BinOp()
        node.left = ast.Constant(1)
        node.op = op_type()
        node.right = ast.Constant(2)

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_BinOp(node)

        assert [file_mutant.text for file_mutant in mutator.mutants] == text_out


class TestAugAssignMutator:
    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["x = 2", "x *= 2"]),
            (ast.Sub, ["x = 2", "x /= 2"]),
            (ast.Mult, ["x = 2", "x += 2"]),
            (ast.Div, ["x = 2", "x -= 2"]),
            (ast.FloorDiv, ["x = 2", "x /= 2"]),
            (ast.Mod, ["x = 2", "x -= 2"]),
            (ast.Pow, ["x = 2", "x *= 2"]),
            (ast.RShift, ["x = 2", "x <<= 2"]),
            (ast.LShift, ["x = 2", "x >>= 2"]),
            (ast.BitOr, ["x = 2", "x &= 2"]),
            (ast.BitXor, ["x = 2", "x |= 2"]),
            (ast.BitAnd, ["x = 2", "x ^= 2"]),
            (ast.MatMult, ["x = 2"]),
        ],
    )
    def test_visit_AugAssign_level_min(self, op_type, text_out, mock_echo):
        mutator = AugAssignMutator(mock.MagicMock(mutator_opts={"operator_level": "min"}), mock_echo)

        node = ast.AugAssign()
        node.target = ast.Name("x")
        node.op = op_type()
        node.value = ast.Constant(2)

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_AugAssign(node)

        assert [file_mutant.text for file_mutant in mutator.mutants] == text_out

    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["x = 2", "x -= 2", "x *= 2"]),
            (ast.Sub, ["x = 2", "x += 2", "x /= 2"]),
            (ast.Mult, ["x = 2", "x /= 2", "x += 2"]),
            (ast.Div, ["x = 2", "x *= 2", "x -= 2"]),
            (ast.FloorDiv, ["x = 2", "x *= 2", "x /= 2"]),
            (ast.Mod, ["x = 2", "x //= 2", "x -= 2"]),
            (ast.Pow, ["x = 2", "x *= 2", "x /= 2"]),
            (ast.RShift, ["x = 2", "x <<= 2"]),
            (ast.LShift, ["x = 2", "x >>= 2"]),
            (ast.BitOr, ["x = 2", "x &= 2", "x ^= 2"]),
            (ast.BitXor, ["x = 2", "x |= 2", "x &= 2"]),
            (ast.BitAnd, ["x = 2", "x ^= 2", "x |= 2"]),
            (ast.MatMult, ["x = 2"]),
        ],
    )
    def test_visit_AugAssign_level_std(self, op_type, text_out, mock_echo):
        mutator = AugAssignMutator(mock.MagicMock(mutator_opts={"operator_level": "std"}), mock_echo)

        node = ast.AugAssign()
        node.target = ast.Name("x")
        node.op = op_type()
        node.value = ast.Constant(2)

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_AugAssign(node)

        assert [file_mutant.text for file_mutant in mutator.mutants] == text_out

    @pytest.mark.parametrize(
        ("op_type", "text_out"),
        [
            (ast.Add, ["x = 2", "x -= 2", "x *= 2", "x /= 2", "x //= 2", "x %= 2", "x **= 2"]),
            (ast.Sub, ["x = 2", "x += 2", "x *= 2", "x /= 2", "x //= 2", "x %= 2", "x **= 2"]),
            (ast.Mult, ["x = 2", "x += 2", "x -= 2", "x /= 2", "x //= 2", "x %= 2", "x **= 2"]),
            (ast.Div, ["x = 2", "x += 2", "x -= 2", "x *= 2", "x //= 2", "x %= 2", "x **= 2"]),
            (ast.FloorDiv, ["x = 2", "x += 2", "x -= 2", "x *= 2", "x /= 2", "x %= 2", "x **= 2"]),
            (ast.Mod, ["x = 2", "x += 2", "x -= 2", "x *= 2", "x /= 2", "x //= 2", "x **= 2"]),
            (ast.Pow, ["x = 2", "x += 2", "x -= 2", "x *= 2", "x /= 2", "x //= 2", "x %= 2"]),
            (ast.RShift, ["x = 2", "x <<= 2", "x |= 2", "x ^= 2", "x &= 2"]),
            (ast.LShift, ["x = 2", "x >>= 2", "x |= 2", "x ^= 2", "x &= 2"]),
            (ast.BitOr, ["x = 2", "x <<= 2", "x >>= 2", "x ^= 2", "x &= 2"]),
            (ast.BitXor, ["x = 2", "x <<= 2", "x >>= 2", "x |= 2", "x &= 2"]),
            (ast.BitAnd, ["x = 2", "x <<= 2", "x >>= 2", "x |= 2", "x ^= 2"]),
            (ast.MatMult, ["x = 2"]),
        ],
    )
    def test_visit_AugAssign_level_max(self, op_type, text_out, mock_echo):
        mutator = AugAssignMutator(mock.MagicMock(mutator_opts={"operator_level": "max"}), mock_echo)

        node = ast.AugAssign()
        node.target = ast.Name("x")
        node.op = op_type()
        node.value = ast.Constant(2)

        node.lineno = 1
        node.col_offset = 1
        node.end_lineno = 1
        node.end_col_offset = 1

        mutator.visit_AugAssign(node)

        assert [file_mutant.text for file_mutant in mutator.mutants] == text_out
