"""Various utility functions."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING, Callable
from zipfile import ZipFile

from wcmatch.pathlib import Path

if TYPE_CHECKING:
    import pathlib

    from .config import PoodleConfigData


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


def files_list_for_source_folders(config_data: PoodleConfigData) -> dict[pathlib.Path, list[pathlib.Path]]:
    """Build map of Folder to all files in folder to include in zips."""
    return {
        folder: files_list_for_folder(
            folder=folder,
            match_glob="*",
            flags=config_data.file_copy_flags,
            filter_globs=config_data.file_copy_filters,
        )
        for folder in config_data.source_folders
    }


def create_temp_zips(config_data: PoodleConfigData, next_num: Callable) -> None:
    """Create a temporary zip file for each folder in source_folders."""
    folder_zips = {}
    config_data.work_folder.mkdir(parents=True, exist_ok=True)
    for folder, files in files_list_for_source_folders(config_data).items():
        zip_file = config_data.work_folder / ("src-" + next_num() + ".zip")
        logger.info("Creating zip file: %s", zip_file)
        folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                logger.info("Adding file: %s", file)
                target_zip.write(file)
    return folder_zips


def delete_folder(folder: pathlib.Path, config_data: PoodleConfigData) -> None:
    """Delete a folder."""
    if folder.exists() and not config_data.skip_delete_folder:
        logger.info("delete %s", folder)
        shutil.rmtree(folder)
