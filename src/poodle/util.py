"""Various utility functions."""

from __future__ import annotations

import logging
import re
from io import StringIO
from pprint import pprint
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

from .data_types import MutantTrialResult, PoodleWork, TestingSummary

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def files_list_for_folder(glob: str, filter_regex: list[str], folder: Path) -> list[Path]:
    """Retrieve list of all files in specified folder.

    Search recursively for files matching glob.
    Remove files matching any of the filter_regex values.
    """
    files = list(folder.rglob(glob))

    for regex in filter_regex:
        files = [file for file in files if not re.match(regex, file.name)]

    logger.debug("folder=%s glob='%s' filters=%s files=%s", folder, glob, filter_regex, files)
    return files


def target_copy_files(work: PoodleWork) -> dict[Path, list[Path]]:
    """Build map of Folder to all files in folder to include in zips."""
    logger.debug("START")
    return {
        folder: files_list_for_folder(
            "*",
            work.config.file_copy_filters,
            folder,
        )
        for folder in work.config.source_folders
    }


def create_temp_zips(work: PoodleWork) -> None:
    """Create a temporary zip file for each folder in source_folders."""
    work.config.work_folder.mkdir(parents=True, exist_ok=True)
    for folder, files in target_copy_files(work).items():
        zip_file = work.config.work_folder / ("src-" + work.next_num() + ".zip")
        logger.info("Creating zip file: %s", zip_file)
        work.folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                target_zip.write(file)


def update_summary(summary: TestingSummary, result: MutantTrialResult) -> None:
    """Update TestingSummary stats using provided MutantTrialResult."""
    summary.tested += 1
    if result.passed:
        summary.found += 1
    elif result.reason_code == MutantTrialResult.RC_NOT_FOUND:
        summary.not_found += 1
    elif result.reason_code == MutantTrialResult.RC_TIMEOUT:
        summary.timeout += 1
    else:
        summary.errors += 1


def dynamic_import(object_to_import: str) -> Any:  # noqa: ANN401
    """Import an Object represented by provided python name."""
    logger.debug("Import object: %s", object_to_import)
    parts = object_to_import.split(".")
    module_str = ".".join(parts[:-1])
    obj_def = parts[-1:][0]
    module = __import__(module_str, fromlist=[obj_def])
    return getattr(module, obj_def)


def pprint_str(obj: Any) -> str:  # noqa: ANN401
    """Pretty Print an object to a string."""
    out = StringIO()
    pprint(obj, stream=out, width=150)  # noqa: T203
    return out.getvalue()
