import ast
import multiprocessing
import re
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from pprint import pprint
from zipfile import ZipFile

from click import echo

from poodle import mutators
from poodle.data import PoodleConfig, PoodleMutant, PoodleTestResult, PoodleWork
from poodle.runners import command_line_runner


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

    shutil.rmtree(config.work_folder)


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
    result = test_mutant(
        work.config,
        work.folder_zips[folder],
        PoodleMutant(
            source_folder=folder,
        ),
        work.next_num(),
        command_line_runner,
    )
    if result.test_passed:  # not expected
        echo("FAILED")
        raise Exception("Clean Run Failed", result.reason_desc)
    else:
        echo(f"PASSED ({(datetime.now()-start)})")


def test_mutants(work: PoodleWork, mutants: list[PoodleMutant]) -> list[PoodleTestResult]:
    start = datetime.now()
    echo("Testing mutants")
    inputs = [
        (
            work.config,
            work.folder_zips[mutant.source_folder],
            mutant,
            work.next_num(),
            command_line_runner,
        )
        for mutant in mutants
    ]
    with multiprocessing.Pool() as pool:
        test_runs = pool.starmap_async(test_mutant, inputs)
        results = test_runs.get()
    echo(f"DONE ({(datetime.now()-start)})")
    pprint(results)


def test_mutant(
    config: PoodleConfig,
    folder_zip: Path,
    mutant: PoodleMutant,
    run_id: str,
    runner,
) -> PoodleTestResult:
    run_folder = config.work_folder / ("run-" + run_id)
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

    result = runner(
        config=config,
        run_folder=run_folder,
        mutant=mutant,
    )

    shutil.rmtree(run_folder)

    return result
