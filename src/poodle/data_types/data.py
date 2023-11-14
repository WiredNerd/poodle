"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class PoodleConfig:
    """Configuration options resolved from command line and config files."""

    config_file: Path | None
    source_folders: list[Path]
    file_filters: list[str]
    file_copy_filters: list[str]
    work_folder: Path

    mutator_opts: dict
    skip_mutators: list[str]
    add_mutators: list[Any]

    runner: str
    runner_opts: dict


@dataclass
class FileMutation:
    """Mutation instructions for the current file."""

    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    text: str


@dataclass
class Mutant(FileMutation):
    """Mutation instructions for a specific file and folder."""

    source_folder: Path
    source_file: Path | None


@dataclass
class MutantTrialResult:
    """Mutation Trial Result for a Mutant."""

    passed: bool
    reason_code: str
    reason_desc: str | None = None

    RC_FOUND = "mutant_found"
    RC_NOT_FOUND = "mutant_not_found"
    RC_TIMEOUT = "timeout"
    RC_INCOMPLETE = "incomplete"
    RC_OTHER = "other"


@dataclass
class MutantTrial:
    """Trial Result for a Mutant."""

    mutant: Mutant
    result: MutantTrialResult
