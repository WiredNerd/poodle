"""Various utility functions."""

from __future__ import annotations

import logging
import re
from io import StringIO
from pprint import pprint
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

if TYPE_CHECKING:
    from pathlib import Path

    from .data_types import PoodleWork

logger = logging.getLogger(__name__)


def files_list_for_folder(glob: str, filter_regex: list[str], folder: Path) -> list[Path]:
    """Retrieve list of all files in specified folder.

    Search recursively for files matching glob.
    Remove files matching any of the filter_regex values.
    """
    logger.debug("files_list_for_folder glob=%s filter_regex=%s folder=%s", glob, filter_regex, folder)

    files = list(folder.rglob(glob))

    for regex in filter_regex:
        files = [file for file in files if not any(re.search(regex, part) for part in file.parts)]

    logger.debug("files_list_for_folder results: folder=%s files=%s", folder, files)
    return files


def files_list_for_source_folders(work: PoodleWork) -> dict[Path, list[Path]]:
    """Build map of Folder to all files in folder to include in zips."""
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
    for folder, files in files_list_for_source_folders(work).items():
        zip_file = work.config.work_folder / ("src-" + work.next_num() + ".zip")
        logger.info("Creating zip file: %s", zip_file)
        work.folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                target_zip.write(file)


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
