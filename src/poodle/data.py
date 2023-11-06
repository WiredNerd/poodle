from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PoodleConfig:
    config_file: Path | None
    source_folders: list[Path]
    file_filters: list[str]
    work_folder: Path
    runner_opts: dict
    mutator_opts: dict


class PoodleWork:
    def __init__(self, config: PoodleConfig):
        self.config = config
        self.folder_zips: dict[str, Path] = {}
        self.num_seq = self.number_sequence()

    def next_num(self):
        return str(next(self.num_seq))

    def number_sequence(self):
        i = 1
        while True:
            yield i
            i += 1


@dataclass
class FileMutant:
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    text: str


@dataclass
class PoodleMutant:
    source_folder: Path
    source_file: Path | None = None
    lineno: int | None = None
    col_offset: int | None = None
    end_lineno: int | None = None
    end_col_offset: int | None = None
    text: str | None = None

    @classmethod
    def from_file_mutant(cls, source_folder: Path, source_file: Path, file_mutant: FileMutant):
        return cls(
            source_folder=source_folder,
            source_file=source_file,
            lineno=file_mutant.lineno,
            col_offset=file_mutant.col_offset,
            end_lineno=file_mutant.end_lineno,
            end_col_offset=file_mutant.end_col_offset,
            text=file_mutant.text,
        )


@dataclass
class PoodleTestResult:
    test_passed: bool
    reason_code: str
    reason_desc: str | None = None

    RC_FOUND = "mutant_found"
    RC_NOT_FOUND = "mutant_not_found"
    RC_TIMEOUT = "timeout"
    RC_INCOMPLETE = "incomplete"
    RC_OTHER = "other"
