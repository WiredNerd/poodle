from __future__ import annotations

import logging
import shutil

import click

from . import PoodleInputError, PoodleTrialRunError
from .data_types import PoodleConfig, PoodleWork
from .mutate import create_mutants_for_all_mutators, initialize_mutators
from .report import generate_reporters
from .run import clean_run_each_source_folder, get_runner, run_mutant_trails
from .util import create_temp_zips, pprint_str

logger = logging.getLogger(__name__)


def run(config: PoodleConfig):
    try:
        work = PoodleWork(config)  # sets logging defaults
        logger.info("\n" + pprint_str(config))

        if config.work_folder.exists():
            logger.info("delete %s", config.work_folder)
            shutil.rmtree(config.work_folder)

        create_temp_zips(work)

        work.mutators = initialize_mutators(work)
        work.runner = get_runner(config)
        work.reporters = list(generate_reporters(config))

        mutants = create_mutants_for_all_mutators(work)
        work.echo(f"Identified {len(mutants)} mutants")

        clean_run_each_source_folder(work)
        results = run_mutant_trails(work, mutants)

        summary = results.summary
        summary.trials = len(results.mutant_trials)
        if summary.trials > 0:
            summary.success_rate = round(summary.found / summary.trials, 1)

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
