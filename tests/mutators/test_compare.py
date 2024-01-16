import ast
from unittest import mock

import pytest

from poodle.mutators.mutator_compare import ComparisonMutator


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


class TestComparisonMutator:
    def test_init(self, mock_echo):
        config = mock.MagicMock(mutator_opts={})
        mutator = ComparisonMutator(config=config, echo=mock_echo, other="value")
        assert mutator.config == config
        assert mutator.mutants == []
        assert mutator.mutator_name == "Compare"
        assert mutator.filter_patterns == [
            r"__name__ == '__main__'",
        ]

    def test_init_patterns(self, mock_echo):
        config = mock.MagicMock(mutator_opts={"compare_filters": ["ignore1", "ignore2"]})
        mutator = ComparisonMutator(config=config, echo=mock_echo, other="value")
        assert mutator.config == config
        assert mutator.mutants == []
        assert mutator.mutator_name == "Compare"
        assert mutator.filter_patterns == [
            r"__name__ == '__main__'",
            "ignore1",
            "ignore2",
        ]

    @pytest.mark.parametrize(
        ("source", "mutants"),
        [
            ("a == b", ["a != b"]),
            ("a != b", ["a == b"]),
            ("a < b", ["a >= b", "a <= b"]),
            ("a <= b", ["a > b", "a < b"]),
            ("a > b", ["a <= b", "a >= b"]),
            ("a >= b", ["a < b", "a > b"]),
            ("a is None", ["a is not None"]),
            ("a is not None", ["a is None"]),
            ("a in d", ["a not in d"]),
            ("a not in d", ["a in d"]),
            ("a or d", ["a and d"]),
            ("a and d", ["a or d"]),
        ],
    )
    def test_create_mutations_eq(self, source, mutants, mock_echo):
        mutator = ComparisonMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        file_mutants = mutator.create_mutations(ast.parse(source))

        assert len(file_mutants) == len(mutants)

        for i in range(len(mutants)):
            assert file_mutants[i].lineno == 1
            assert file_mutants[i].end_lineno == 1
            assert file_mutants[i].col_offset == 0
            assert file_mutants[i].end_col_offset == len(source)
            assert file_mutants[i].text == mutants[i]

    def test_filter_compare(self, mock_echo):
        mutator_opts = {"compare_filters": ["special.* < 4", "special.* in .*", "x or y"]}
        mutator = ComparisonMutator(config=mock.MagicMock(mutator_opts=mutator_opts), echo=mock_echo)

        if_main = "if __name__ == '__main__':\n   pass"
        assert mutator.create_mutations(ast.parse(if_main)) == []

        if_obj_lt = "if special_obj < 4:\n   pass"
        assert mutator.create_mutations(ast.parse(if_obj_lt)) == []

        if_or = "if special_obj2 in obj_list:\n   pass"
        assert mutator.create_mutations(ast.parse(if_or)) == []

        if_or = "if x or y:\n   pass"
        assert mutator.create_mutations(ast.parse(if_or)) == []

    def test_is_annotation(self, mock_echo):
        mutator = ComparisonMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        module = "\n".join(  # noqa: FLY002
            [
                "def example(y:int or str)-> int or str:",
                "    x:int or str = y",
                "    return y",
            ],
        )
        file_mutants = mutator.create_mutations(ast.parse(module))

        assert file_mutants == []

    def test_unrecognized_op(self, mock_echo):
        mutator = ComparisonMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        bool_op = ast.BoolOp()
        bool_op.op = ast.Constant()

        file_mutants = mutator.create_mutations(bool_op)

        assert file_mutants == []
