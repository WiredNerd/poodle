from __future__ import annotations

class PoodleTestingFailedError(Exception):
    """Poodle testing failed."""


class PoodleNoMutantsFoundError(Exception):
    """Poodle could not find any mutants to test."""


class PoodleInputError(ValueError):
    """An input value from Command Line, poodle_config.py, or a config file was invalid."""


class PoodleTrialRunError(Exception):
    """An unexpected error occurred when running a mutation trial or clean run."""
