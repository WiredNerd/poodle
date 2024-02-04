"""Utilities for working with configuration files."""

from __future__ import annotations

import importlib
import sys
from contextlib import suppress
from functools import cache
from pathlib import Path
from types import ModuleType


@cache
def get_poodle_config() -> ModuleType | None:
    """Get poodle_config module if it exists."""
    if "poodle_config" in sys.modules:
        return sys.modules["poodle_config"]
    with suppress(ModuleNotFoundError):
        cwd_path = str(Path.cwd())
        if cwd_path not in sys.path:
            sys.path.append(str(Path.cwd()))
        return importlib.import_module("poodle_config")
    return None
