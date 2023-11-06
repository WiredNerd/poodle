"""Poodle Mutation Testing."""

from poodle.data import Mutant, PoodleConfig
from poodle.mutators import PoodleMutator


class PoodleInputError(ValueError):
    """An input value from Command Line, poodle_config.py, or a config file was invalid."""
