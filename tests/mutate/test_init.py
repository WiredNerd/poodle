from unittest import mock

import pytest

from poodle.data import FileMutation, PoodleConfig
from poodle.mutate import Mutator, create_mutations


@pytest.fixture()
def mock_print():
    with mock.patch("builtins.print") as mock_print:
        yield mock_print


def test_create_mutations():
    assert create_mutations(config=None, parsed_ast=None, other=None) is None


class TestMutator:
    class DummyMutator(Mutator):
        def create_mutations(self, **_) -> list[FileMutation]:
            return []

    def test_abstract(self):
        with pytest.raises(TypeError, match="^Can't instantiate abstract class.*create_mutations*"):
            Mutator(config=mock.MagicMock(spec=PoodleConfig))

    def test_init(self):
        config = mock.MagicMock(spec=PoodleConfig)
        mutator = self.DummyMutator(config=config, other="value")

        assert mutator.config == config
