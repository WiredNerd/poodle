"""Poodle core run process."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING

import click

from . import PoodleInputError, PoodleTrialRunError
from .data_types import MutantTrial, PoodleConfig, PoodleWork
from .mutate import create_mutants_for_all_mutators, initialize_mutators
from .report import generate_reporters
from .run import clean_run_each_source_folder, get_runner, run_mutant_trails
from .util import create_temp_zips, pprint_str

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def main(config: PoodleConfig) -> None:
    """Poodle core run process."""
    try:
        work = PoodleWork(config)  # sets logging defaults
        logger.info("\n%s", pprint_str(config))

        if config.work_folder.exists():
            logger.info("delete %s", config.work_folder)
            shutil.rmtree(config.work_folder)

        create_temp_zips(work)

        work.mutators = initialize_mutators(work)
        work.runner = get_runner(config)
        work.reporters = list(generate_reporters(config))

        mutants = create_mutants_for_all_mutators(work)
        work.echo(f"Identified {len(mutants)} mutants")

        clean_run_results = clean_run_each_source_folder(work)
        timeout = calc_timeout(config, clean_run_results)
        results = run_mutant_trails(work, mutants, timeout)

        for reporter in work.reporters:
            reporter(config=config, echo=work.echo, testing_results=results)

        logger.info("delete %s", config.work_folder)
        shutil.rmtree(config.work_folder)
    except PoodleInputError as err:
        for arg in err.args:
            click.echo(arg)
    except PoodleTrialRunError as err:
        for arg in err.args:
            click.echo(arg)


def calc_timeout(config: PoodleConfig, clean_run_results: dict[Path, MutantTrial]) -> float:
    """Determine timeout value to use in runner."""
    max_clean_run = max([trial.duration for trial in clean_run_results.values()])
    # TODO: config.timeout_multiplier
    return max(float(max_clean_run) * 10, config.min_timeout)
