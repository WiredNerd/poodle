import ast
from unittest import mock

import pytest

from poodle.mutators.unary_op import UnaryOperationMutator


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


class TestUnaryOperationMutator:
    @pytest.mark.parametrize(
        ("source", "mutant_text"),
        [
            ("+3", "-3"),
            ("-3", "+3"),
            ("not a", "a"),
            ("~a", "a"),
        ],
    )
    def test_create_mutations(self, source, mutant_text, mock_echo):
        mutator = UnaryOperationMutator(config=mock.MagicMock(mutator_opts={}), echo=mock_echo)

        file_mutants = mutator.create_mutations(ast.parse(source))

        assert file_mutants[0].lineno == 1
        assert file_mutants[0].end_lineno == 1
        assert file_mutants[0].col_offset == 0
        assert file_mutants[0].end_col_offset == len(source)
        assert file_mutants[0].text == mutant_text
