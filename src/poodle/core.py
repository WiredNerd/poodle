import ast
import concurrent.futures
import re
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
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
    results = test_mutants(work, mutants)

    summary(results)

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

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                test_mutant,
                work.config,
                work.folder_zips[mutant.source_folder],
                mutant,
                work.next_num(),
                command_line_runner,
            )
            for mutant in mutants
        ]

        stats = {
            "tested": 0,
            "found": 0,
            "not_found": 0,
            "timeout": 0,
            "errors": 0,
        }
        tests = len(mutants)
        for future in concurrent.futures.as_completed(futures):
            if future.cancelled():
                echo("Canceled")
            else:
                result: PoodleTestResult = future.result()
                update_stats(stats, result)
            echo(
                f'COMPLETED {stats["tested"]:>4}/{tests:<4}'
                f'\tFOUND {stats["found"]:>4}'
                f'\tNOT FOUND {stats["not_found"]:>4}'
                f'\tTIMEOUT {stats["timeout"]:>4}'
                f'\tERRORS {stats["errors"]:>4}'
            )

    echo(f"DONE ({(datetime.now()-start)})")

    return [future.result() for future in futures]


def update_stats(stats: dict, result: PoodleTestResult):
    stats["tested"] += 1
    if result.test_passed:
        stats["found"] += 1
    elif result.reason_code == PoodleTestResult.RC_NOT_FOUND:
        stats["not_found"] += 1
    elif result.reason_code == PoodleTestResult.RC_TIMEOUT:
        stats["timeout"] += 1
    else:
        stats["errors"] += 1


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

    result: PoodleTestResult = runner(
        config=config,
        run_folder=run_folder,
        mutant=mutant,
    )

    shutil.rmtree(run_folder)

    return result


def summary(results: list[PoodleTestResult]):
    stats = {
        "tested": 0,
        "found": 0,
        "not_found": 0,
        "timeout": 0,
        "errors": 0,
    }
    tests = len(results)
    for result in results:
        update_stats(stats, result)

    echo("Results Summary")
    echo(f'Testing found {stats["found"]/tests:.1%} of Mutants')
    if stats["not_found"]:
        echo(f' - {stats["not_found"]} mutant(s) were not found')
    if stats["timeout"]:
        echo(f' - {stats["timeout"]} mutant(s) caused testing to timeout.')
    if stats["errors"]:
        echo(f' - {stats["errors"]} mutant(s) could not be tested due to an error.')
