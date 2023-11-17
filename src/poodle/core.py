from __future__ import annotations

import shutil
from zipfile import ZipFile

from click import echo

from .data_types import PoodleConfig, PoodleWork
from .mutate import create_mutants_for_all_mutators, initialize_mutators
from .report import get_reporters
from .run import clean_run_each_source_folder, get_runner, run_mutant_trails
from .util import files_list_for_folder


def run(config: PoodleConfig):
    work = PoodleWork(config)

    if config.work_folder.exists():
        shutil.rmtree(config.work_folder)

    create_temp_zips(work)

    work.mutators = initialize_mutators(work)
    work.runner = get_runner(config)
    work.reporters = get_reporters(config)

    mutants = create_mutants_for_all_mutators(work)
    echo(f"Identified {len(mutants)} mutants")

    clean_run_each_source_folder(work)
    results = run_mutant_trails(work, mutants)

    summary = results.summary
    summary.trials = len(results.mutant_trials)
    if summary.trials > 0:
        summary.success_rate = round(summary.found / summary.trials, 1)

    for reporter in work.reporters:
        reporter(config=config, testing_results=results)

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
