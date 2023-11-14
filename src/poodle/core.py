from __future__ import annotations

import shutil
from zipfile import ZipFile

from click import echo

from .mutate import create_mutants_for_all_mutators, initialize_mutators
from .run import clean_run_each_source_folder, get_runner, run_mutant_trails
from .types import MutantTrial, PoodleConfig, PoodleWork
from .util import files_list_for_folder, update_stats


def run(config: PoodleConfig):
    work = PoodleWork(config)

    if config.work_folder.exists():
        shutil.rmtree(config.work_folder)

    create_temp_zips(work)

    work.mutators = initialize_mutators(work)
    work.runner = get_runner(config)

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
            src = mutant.source_file.resolve() if mutant.source_file else "None"
            echo(f"Mutant: {src}:{mutant.lineno}")
            echo(mutant.text)
            echo(f"Result: {result.reason_code}")
            if result.reason_desc:
                echo(result.reason_desc)
            echo("")
