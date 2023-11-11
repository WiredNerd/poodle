"""Poodle Mutation Testing."""

from __future__ import annotations

from poodle.data import FileMutation, PoodleConfig
from poodle.mutate import Mutator


class PoodleInputError(ValueError):
    """An input value from Command Line, poodle_config.py, or a config file was invalid."""


import importlib
import os
import sys
from contextlib import suppress

try:
    import tomllib  # type: ignore [import-not-found]
except ModuleNotFoundError:  # < py3.11
    import tomli as tomllib  # type: ignore [no-redef]


poodle_config: any = None
with suppress(ImportError):
    sys.path.append(os.getcwd())
    poodle_config = importlib.import_module("poodle_config")
