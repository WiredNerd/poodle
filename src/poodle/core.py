import ast
import multiprocessing
import os
import re
import shlex
import shutil
import subprocess
from ast import Module
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from click import echo

from poodle import mutators
from poodle.data import PoodleConfig, PoodleMutant, PoodleWork


def run(config: PoodleConfig):
    work = PoodleWork(config)

    if config.work_folder.exists():
        shutil.rmtree(config.work_folder)

    targets = target_files(work)
    create_temp_zips(work, targets)

    mutants = create_mutants(work, targets)
    echo(f"Identified {len(mutants)} mutants")

    test_clean_runs(work, targets)
    test_mutants(work, mutants)

    # shutil.rmtree(config.work_folder)


def target_files(work: PoodleWork):
    return {folder: target_files_for_folder(work, folder) for folder in work.config.source_folders}


def target_files_for_folder(work: PoodleWork, folder: Path):
    target_files = [x for x in folder.rglob("*.py")]

    for filter in work.config.file_filters:
        target_files = [file for file in target_files if not re.match(filter, file.stem)]

    return target_files


def create_mutants(work: PoodleWork, targets: dict):
    return [
        mutant
        for folder, files in targets.items()
        for file in files
        for mutant in create_mutants_for_file(
            work,
            folder,
            file,
        )
    ]


def create_mutants_for_file(work: PoodleWork, folder: Path, file: Path):
    parsed_ast = ast.parse(file.read_bytes(), file)
    bin_op_mut = mutators.BinaryOperationMutator(work.config)
    file_mutants = bin_op_mut.create_mutants(deepcopy(parsed_ast))

    return [PoodleMutant.from_file_mutant(folder, file, file_mutant) for file_mutant in file_mutants]


def create_temp_zips(work: PoodleWork, targets: dict):
    work.config.work_folder.mkdir(parents=True, exist_ok=True)
    for folder, files in targets.items():
        zip_file = work.config.work_folder / ("src-" + work.next_num() + ".zip")
        work.folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                target_zip.write(file)


def test_clean_runs(work: PoodleWork, targets: dict):
    return [test_clean_run(work, folder) for folder in targets]


def test_clean_run(work: PoodleWork, folder: Path):
    start = datetime.now()
    echo(f"Testing clean run of folder '{folder}'...", nl=False)
    (mutation_found, test_timeout, reason) = test_mutant(
        work.config.work_folder,
        work.folder_zips[folder],
        PoodleMutant(
            source_folder=folder,
        ),
        work.next_num(),
    )
    if mutation_found:  # not expected
        echo("FAILED")
        raise Exception("Clean Run Failed", folder, reason)
    else:
        echo(f"PASSED ({(datetime.now()-start)})")


def test_mutants(work: PoodleWork, mutants: list[PoodleMutant]):
    start = datetime.now()
    echo("Testing mutants")
    inputs = [
        (
            work.config.work_folder,
            work.folder_zips[mutant.source_folder],
            mutant,
            work.next_num(),
        )
        for mutant in mutants
    ]
    with multiprocessing.Pool() as pool:
        test_runs = pool.starmap_async(test_mutant, inputs)
        results = test_runs.get()
    echo(f"DONE ({(datetime.now()-start)})")
    echo(results)


def test_mutant(work_folder: Path, folder_zip: Path, mutant: PoodleMutant, run_id: str):
    run_folder = work_folder / ("run-" + run_id)
    run_folder.mkdir()

    with ZipFile(folder_zip, "r") as zip_file:
        zip_file.extractall(run_folder)

    if mutant.source_file:
        target_file = Path(run_folder / mutant.source_file)
        file_lines = target_file.read_text("utf-8").splitlines(keepends=True)

        prefix = file_lines[mutant.lineno - 1][: mutant.col_offset]
        suffix = file_lines[mutant.end_lineno - 1][mutant.end_col_offset :]

        file_lines[mutant.lineno - 1] = prefix + mutant.text + suffix
        for _ in range(mutant.lineno, mutant.end_lineno):
            file_lines.pop(mutant.lineno)

        target_file.write_text(data="".join(file_lines), encoding="utf-8")

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = os.pathsep.join(
        [
            str(run_folder / mutant.source_folder),
            run_env.get("PYTHONPATH", ""),
        ]
    )
    run_env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        shlex.split("pytest -o pythonpath="),
        env=run_env,
        capture_output=True,
    )

    # shutil.rmtree(run_folder)

    # pass: bool, timeout: bool, reason: str
    return (result.returncode != 0, False, str(result.returncode))
