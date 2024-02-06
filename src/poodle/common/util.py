"""Various utility functions."""

from __future__ import annotations

import difflib
import json
from copy import deepcopy
from io import StringIO
from pprint import pprint
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import PoodleConfigData
    from .data import CleanRunTrial, Mutant, PoodleSerialize


def pprint_to_str(obj: Any) -> str:  # noqa: ANN401
    """Pretty Print an object to a string."""
    out = StringIO()
    pprint(obj, stream=out, width=150)  # noqa: T203
    return out.getvalue()


def mutate_lines(mutant: Mutant, file_lines: list[str]) -> list[str]:
    """Apply mutation to list of lines from file."""
    mut_lines = deepcopy(file_lines)
    prefix = mut_lines[mutant.lineno - 1][: mutant.col_offset]
    suffix = mut_lines[mutant.end_lineno - 1][mutant.end_col_offset :]

    mut_lines[mutant.lineno - 1] = prefix + mutant.text + suffix
    for _ in range(mutant.lineno, mutant.end_lineno):
        mut_lines.pop(mutant.lineno)

    return mut_lines


def create_unified_diff(mutant: Mutant) -> str | None:
    """Add unified diff to mutant."""
    if mutant.source_file:
        file_lines = mutant.source_file.read_text("utf-8").splitlines(keepends=True)
        file_name = str(mutant.source_file)
        mutant_lines = "".join(mutate_lines(mutant, file_lines)).splitlines(keepends=True)
        return "".join(
            difflib.unified_diff(
                a=file_lines,
                b=mutant_lines,
                fromfile=file_name,
                tofile=f"[Mutant] {file_name}:{mutant.lineno}",
            )
        )
    return None


def display_percent(value: float) -> str:
    """Convert float to string with percent sign."""
    return f"{value * 1000 // 1 / 10:.3g}%"
