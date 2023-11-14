from __future__ import annotations

import concurrent.futures
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from click import echo

from .runners import command_line
from .types import Mutant, MutantTrial, MutantTrialResult, PoodleConfig, PoodleWork
from .util import dynamic_import, update_stats

builtin_runners = {
    "command_line": command_line.runner,
}


def get_runner(config: PoodleWork):
    if config.runner in builtin_runners:
        return builtin_runners[config.runner]

    return dynamic_import(config.runner)


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
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        ),
        work.next_num(),
        work.runner,
    )
    if mutant_trial.result.passed:  # not expected
        echo("FAILED")
        raise Exception("Clean Run Failed", mutant_trial.result.reason_desc)
    else:
        echo(f"PASSED ({(datetime.now()-start)})")


def run_mutant_trails(work: PoodleWork, mutants: list[Mutant]) -> list[MutantTrial]:
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
                work.runner,
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
