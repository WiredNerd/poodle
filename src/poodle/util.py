"""Various utility functions."""

from __future__ import annotations

import logging
from io import StringIO
from pprint import pprint
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

from wcmatch.pathlib import Path

if TYPE_CHECKING:
    import pathlib

    from .data_types import MutantTrial, PoodleConfig, PoodleWork

logger = logging.getLogger(__name__)


def files_list_for_folder(
    folder: pathlib.Path,
    match_glob: str,
    flags: int | None,
    filter_globs: list[str],
) -> list[pathlib.Path]:
    """Retrieve list of files in specified folder.

    Search recursively for files matching match_glob.
    Remove files matching any of the filter_globs values.
    """
    logger.debug("files_list_for_folder folder=%s, match_glob=%s filter_globs=%s", folder, match_glob, filter_globs)

    files: list[pathlib.Path] = list(Path(folder).rglob(match_glob, flags=flags, exclude=filter_globs))  # type: ignore [arg-type]

    logger.debug("files_list_for_folder results: folder=%s files=%s", folder, files)
    return files


def files_list_for_source_folders(work: PoodleWork) -> dict[pathlib.Path, list[pathlib.Path]]:
    """Build map of Folder to all files in folder to include in zips."""
    return {
        folder: files_list_for_folder(
            folder=folder,
            match_glob="*",
            flags=work.config.file_copy_flags,
            filter_globs=work.config.file_copy_filters,
        )
        for folder in work.config.source_folders
    }


def create_temp_zips(work: PoodleWork) -> None:
    """Create a temporary zip file for each folder in source_folders."""
    work.config.work_folder.mkdir(parents=True, exist_ok=True)
    for folder, files in files_list_for_source_folders(work).items():
        zip_file = work.config.work_folder / ("src-" + work.next_num() + ".zip")
        logger.info("Creating zip file: %s", zip_file)
        work.folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                logger.info("Adding file: %s", file)
                target_zip.write(file)


def dynamic_import(object_to_import: str) -> Any:  # noqa: ANN401
    """Import an Object represented by provided python name."""
    logger.debug("Import object: %s", object_to_import)
    parts = object_to_import.split(".")
    module_str = ".".join(parts[:-1])
    obj_def = parts[-1]
    module = __import__(module_str, fromlist=[obj_def])
    return getattr(module, obj_def)


def pprint_str(obj: Any) -> str:  # noqa: ANN401
    """Pretty Print an object to a string."""
    out = StringIO()
    pprint(obj, stream=out, width=150)  # noqa: T203
    return out.getvalue()


def calc_timeout(config: PoodleConfig, clean_run_results: dict[pathlib.Path, MutantTrial]) -> float:
    """Determine timeout value to use in runner."""
    max_clean_run = max([trial.duration for trial in clean_run_results.values()])
    return max(float(max_clean_run) * config.timeout_multiplier, config.min_timeout)
