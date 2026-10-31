# Copyright (c) 2023 WiredNerd
# SPDX-License-Identifier: MIT
"""Various utility functions."""

from __future__ import annotations

import difflib
import json
import logging
import os
import shutil
import stat
from copy import deepcopy
from io import StringIO
from pprint import pprint
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile, ZipInfo

from wcmatch import glob
from wcmatch.pathlib import Path, PurePath

if TYPE_CHECKING:
    import pathlib

    from .data_types import Mutant, MutantTrial, PoodleConfig, PoodleSerialize, PoodleWork

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
    """Build map of Folder to all files in folder to include in zips.

    On POSIX every symlink is listed as itself, for `trial_links` to decide how it is copied:
    directories are listed and then dropped, rather than excluded with NODIR, because NODIR also
    drops a link to a directory, and FOLLOW is ignored, so nothing is listed through a link.
    """
    if os.name != "posix":
        return {
            folder: files_list_for_folder(
                folder=folder,
                match_glob="*",
                flags=work.config.file_copy_flags,
                filter_globs=work.config.file_copy_filters,
            )
            for folder in work.config.source_folders
        }
    flags = work.config.file_copy_flags
    if flags is not None:
        flags &= ~(glob.NODIR | glob.FOLLOW)
    lists = {}
    for folder in work.config.source_folders:
        listed = files_list_for_folder(
            folder=folder,
            match_glob="*",
            flags=flags,
            filter_globs=work.config.file_copy_filters,
        )
        listed += _unlisted_links(folder, listed, flags, work.config.file_copy_filters)
        lists[folder] = [path for path in listed if path.is_symlink() or not path.is_dir()]
    return lists


def _unlisted_links(
    folder: pathlib.Path,
    listed: list[pathlib.Path],
    flags: int | None,
    filter_globs: list[str],
) -> list[pathlib.Path]:
    """Symlinks that rglob drops because they cannot be resolved (a link loop).

    Every directory under the folder is searched, without following links, and each link found
    passes the same flags and filters as a listed path would.
    """
    known = set(listed)
    found: list[pathlib.Path] = []
    for directory, _, names in os.walk(folder):
        for name in names:
            path = Path(directory) / name
            if not path.is_symlink() or path in known:
                continue
            relative = PurePath(str(path.relative_to(folder)))
            if relative.match("*", flags=flags or 0, exclude=filter_globs):
                found.append(path)
    return found


def trial_links(folder: pathlib.Path, files: list[pathlib.Path]) -> dict[pathlib.Path, str]:
    """Give the target text each symlink among a source folder's files gets in a trial folder.

    Every link stays a link, and no target is ever opened. A link whose target is inside the folder
    (or the folder itself) gets the relative path from the link's directory to where the target
    really is, so that it points into the trial, never into the source. Any other link, to a file,
    a directory or a missing target, gets its target as an absolute path: the trial then reads what
    the source reads, and a trial writing through such a link writes the real target, outside the
    trial and outside its cleanup. When that target is in another source folder, the link reads the
    source, not that folder's copy in the trial.

    An existing target is placed where it really is, every link on its way followed. A dangling
    link (a loop included) has nothing to follow: it is placed by its target text alone.
    """
    links: dict[pathlib.Path, str] = {}
    for link in (file for file in files if file.is_symlink()):
        if link.exists():
            root, base, target = (os.path.realpath(path) for path in (folder, link.parent, link))
        else:
            text = os.readlink(link)  # noqa: PTH115 - a dangling target exists only as text
            root, base = (os.path.normpath(os.path.abspath(path)) for path in (folder, link.parent))  # noqa: PTH100
            target = os.path.normpath(os.path.join(base, text))  # noqa: PTH118 - the text, not a path to follow
        if target == root or target.startswith(root + os.sep):
            links[link] = os.path.relpath(target, base)
        else:
            links[link] = target
    return links


def create_temp_zips(work: PoodleWork) -> None:
    """Create a temporary zip file for each folder in source_folders."""
    work.config.work_folder.mkdir(parents=True, exist_ok=True)
    for folder, files in files_list_for_source_folders(work).items():
        links = trial_links(folder, files) if os.name == "posix" else {}
        zip_file = work.config.work_folder / ("src-" + work.next_num() + ".zip")
        logger.info("Creating zip file: %s", zip_file)
        work.folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                target = links.get(file)
                logger.info("Adding file: %s", file)
                if target:
                    # stored as the link itself, its target text as content
                    link = ZipInfo(str(file))
                    link.external_attr = (stat.S_IFLNK | 0o777) << 16
                    target_zip.writestr(link, os.fsencode(target))
                else:
                    target_zip.write(file)


def extract_trial_folder(zip_file: ZipFile, run_folder: pathlib.Path) -> None:
    """Extract a source folder's zip into a trial folder, file modes and symlinks included.

    `extractall` restores neither: every file gets the umask's mode, and a link entry becomes a
    regular file holding its target text. Links are recreated only after everything is extracted,
    so no file is ever written through one.

    Off POSIX the extraction is left as it always was: a read-only mode there would also make the
    trial folder undeletable.
    """
    zip_file.extractall(run_folder)
    if os.name != "posix":
        return
    for info in zip_file.infolist():
        mode = info.external_attr >> 16
        if not mode or info.is_dir():
            continue
        # where `extractall` put it: it drops a drive, a leading "/" and "." / ".." parts, so the
        # entry for an absolute or "../" source folder lands inside run_folder, and joining the raw
        # name would reach outside it - into the source itself for an absolute folder
        parts = PurePath(os.path.splitdrive(info.filename)[1]).parts
        path = run_folder.joinpath(*(part for part in parts if part not in (os.sep, "/", os.curdir, os.pardir)))
        if stat.S_ISLNK(mode):
            target = os.fsdecode(zip_file.read(info))
            path.unlink()
            path.symlink_to(target)
        else:
            path.chmod(stat.S_IMODE(mode))


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


def to_json(obj: PoodleSerialize, indent: int | str | None = None) -> str:
    """Convert dataclass to json string."""
    return json.dumps(obj, indent=indent, default=lambda x: x.to_dict())


def from_json(data: str, datatype: type[PoodleSerialize]) -> PoodleSerialize:
    """Convert json string to dataclass."""
    return datatype(**json.loads(data, object_hook=datatype.from_dict))


def display_percent(value: float) -> str:
    """Convert float to string with percent sign."""
    return f"{value * 1000 // 1 / 10:.3g}%"


def delete_folder(folder: pathlib.Path, config: PoodleConfig) -> None:
    """Delete a folder."""
    if folder.exists() and not config.skip_delete_folder:
        logger.info("delete %s", folder)
        shutil.rmtree(folder)
