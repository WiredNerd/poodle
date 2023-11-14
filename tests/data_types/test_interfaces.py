from unittest import mock

import pytest

from poodle.data_types.data import FileMutation, PoodleConfig
from poodle.data_types.interfaces import Mutator, create_mutations, runner


def test_create_mutations():
    assert create_mutations(config=None, parsed_ast=None, other=None) is None


class TestMutator:
    class DummyMutator(Mutator):
        def create_mutations(self, **_) -> list[FileMutation]:  # type: ignore [override]
            return []

    def test_abstract(self):
        with pytest.raises(TypeError, match="^Can't instantiate abstract class.*create_mutations*"):
            Mutator(config=mock.MagicMock(spec=PoodleConfig))

    def test_init(self):
        config = mock.MagicMock(spec=PoodleConfig)
        mutator = self.DummyMutator(config=config, other="value")

        assert mutator.config == config


def test_runner():
    assert (
        runner(
            config=None,
            run_folder=None,
            mutant=None,
            other="value",
        )
        is None
    )
