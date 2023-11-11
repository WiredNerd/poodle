import concurrent.futures
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from click import echo

from poodle.data import Mutant, MutantTrial, MutantTrialResult, PoodleConfig, PoodleWork
from poodle.mutate.mutate import create_mutants_for_all_mutators, initialize_mutators
from poodle.runners import command_line_runner
from poodle.util import files_list_for_folder


def run(config: PoodleConfig):
    work = PoodleWork(config)

    if config.work_folder.exists():
        shutil.rmtree(config.work_folder)

    create_temp_zips(work)

    work.mutators = initialize_mutators(work)

    mutants = create_mutants_for_all_mutators(work)
    echo(f"Identified {len(mutants)} mutants")

    clean_run_each_source_folder(work)
    results = run_mutant_trails(work, mutants)

    summary(results)
    list_failed(results)

    shutil.rmtree(config.work_folder)


def target_copy_files(work: PoodleWork):
    return {
        folder: files_list_for_folder(
            "*",
            work.config.file_copy_filters,
            folder,
        )
        for folder in work.config.source_folders
    }


def create_temp_zips(work: PoodleWork):
    work.config.work_folder.mkdir(parents=True, exist_ok=True)
    for folder, files in target_copy_files(work).items():
        zip_file = work.config.work_folder / ("src-" + work.next_num() + ".zip")
        work.folder_zips[folder] = zip_file
        with ZipFile(zip_file, "w") as target_zip:
            for file in files:
                target_zip.write(file)


def clean_run_each_source_folder(work: PoodleWork):
    return [clean_run_trial(work, folder) for folder in work.config.source_folders]


def clean_run_trial(work: PoodleWork, folder: Path):
    start = datetime.now()
    echo(f"Testing clean run of folder '{folder}'...", nl=False)
    mutant_trial = run_mutant_trial(
        work.config,
        work.folder_zips[folder],
        Mutant(
            source_folder=folder,
            source_file=None,
            lineno=None,
            col_offset=None,
            end_lineno=None,
            end_col_offset=None,
            text=None,
        ),
        work.next_num(),
        command_line_runner,
    )
    if mutant_trial.result.passed:  # not expected
        echo("FAILED")
        raise Exception("Clean Run Failed", mutant_trial.result.reason_desc)
    else:
        echo(f"PASSED ({(datetime.now()-start)})")


def run_mutant_trails(work: PoodleWork, mutants: list[Mutant]) -> list[MutantTrialResult]:
    start = datetime.now()
    echo("Testing mutants")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                run_mutant_trial,
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
        num_trials = len(mutants)
        for future in concurrent.futures.as_completed(futures):
            if future.cancelled():
                echo("Canceled")
            else:
                mutant_trial: MutantTrial = future.result()
                update_stats(stats, mutant_trial.result)
            echo(
                f'COMPLETED {stats["tested"]:>4}/{num_trials:<4}'
                f'\tFOUND {stats["found"]:>4}'
                f'\tNOT FOUND {stats["not_found"]:>4}'
                f'\tTIMEOUT {stats["timeout"]:>4}'
                f'\tERRORS {stats["errors"]:>4}'
            )

    echo(f"DONE ({(datetime.now()-start)})")

    return [future.result() for future in futures]


def update_stats(stats: dict, result: MutantTrialResult):
    stats["tested"] += 1
    if result.passed:
        stats["found"] += 1
    elif result.reason_code == MutantTrialResult.RC_NOT_FOUND:
        stats["not_found"] += 1
    elif result.reason_code == MutantTrialResult.RC_TIMEOUT:
        stats["timeout"] += 1
    else:
        stats["errors"] += 1


def run_mutant_trial(
    config: PoodleConfig,
    folder_zip: Path,
    mutant: Mutant,
    run_id: str,
    runner,
) -> MutantTrial:
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

    result: MutantTrialResult = runner(
        config=config,
        run_folder=run_folder,
        mutant=mutant,
    )

    shutil.rmtree(run_folder)

    return MutantTrial(mutant, result)


def summary(mutant_trials: list[MutantTrial]):
    if not mutant_trials:
        echo("No mutants found to test.")
        return
    stats = {
        "tested": 0,
        "found": 0,
        "not_found": 0,
        "timeout": 0,
        "errors": 0,
    }
    num_trials = len(mutant_trials)
    for trial in mutant_trials:
        update_stats(stats, trial.result)

    echo("Results Summary")
    echo(f'Testing found {stats["found"]/num_trials:.1%} of Mutants')
    if stats["not_found"]:
        echo(f' - {stats["not_found"]} mutant(s) were not found')
    if stats["timeout"]:
        echo(f' - {stats["timeout"]} mutant(s) caused trial to timeout.')
    if stats["errors"]:
        echo(f' - {stats["errors"]} mutant(s) could not be tested due to an error.')


def list_failed(mutant_trials: list[MutantTrial]):
    failed_trials = [trial for trial in mutant_trials if not trial.result.passed]
    if failed_trials:
        echo("\nFailed Trials:")
        for trial in failed_trials:
            mutant = trial.mutant
            result = trial.result
            echo(f"Mutant: {mutant.source_file.resolve()}:{mutant.lineno}")
            echo(mutant.text)
            echo(f"Result: {result.reason_code}")
            if result.reason_desc:
                echo(result.reason_desc)
            echo("")
