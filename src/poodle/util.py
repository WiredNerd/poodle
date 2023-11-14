"""Various utility functions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .types import MutantTrialResult


def files_list_for_folder(glob: str, filter_regex: list[str], folder: Path) -> list[Path]:
    """Retrieve list of all files in specified folder.

    Search recursively for files matching glob.
    Remove files matching any of the filter_regex values.
    """
    files = list(folder.rglob(glob))

    for regex in filter_regex:
        files = [file for file in files if not re.match(regex, file.name)]

    return files


def update_stats(stats: dict, result: MutantTrialResult):
    stats["tested"] += 1
    if result.passed:
        stats["found"] += 1
    elif result.reason_code == MutantTrialResult.RC_NOT_FOUND:
        stats["not_found"] += 1
    elif result.reason_code == MutantTrialResult.RC_TIMEOUT:
        stats["timeout"] += 1
    else:
        stats["errors"] += 1


def dynamic_import(object_to_import: str) -> Any:
    parts = object_to_import.split(".")
    module_str = ".".join(parts[:-1])
    obj_def = parts[-1:][0]
    module = __import__(module_str, fromlist=[obj_def])
    return getattr(module, obj_def)
