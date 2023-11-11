"""Create Mutants."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod

from poodle.data import FileMutation, PoodleConfig


def create_mutations(config: PoodleConfig, parsed_ast: ast.Module, **_) -> list[FileMutation]:
    """Create a list of Mutants for the provided parsed Module.

    This will be called once with parsed ast for each Module.
    """


class Mutator(ABC):
    """Abstract class for Mutators."""

    def __init__(self, config: PoodleConfig, **_) -> PoodleConfig:
        """Initialize PoodleMutator."""
        self.config = config

    @abstractmethod
    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Create a list of Mutants for the provided parsed Module.

        This will be called once with parsed ast for each Module.
        """
