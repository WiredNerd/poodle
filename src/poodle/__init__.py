"""Poodle Mutation Test Tool."""

from __future__ import annotations

import importlib
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

__version__ = "1.3.1"


class PoodleTestingFailedError(Exception):
    """Poodle testing failed."""


class PoodleNoMutantsFoundError(Exception):
    """Poodle could not find any mutants to test."""


class PoodleInputError(ValueError):
    """An input value from Command Line, poodle_config.py, or a config file was invalid."""


class PoodleTrialRunError(Exception):
    """An unexpected error occurred when running a mutation trial or clean run."""


try:
    import tomllib  # type: ignore [import-not-found]
except ModuleNotFoundError:  # < py3.11
    import tomli as tomllib  # type: ignore [no-redef]


poodle_config: Any = None
with suppress(ImportError):
    sys.path.append(str(Path.cwd()))
    poodle_config = importlib.import_module("poodle_config")
