"""Basic Mutation Test Result Reporters."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import click

from poodle.data_types import MutantTrialResult, PoodleConfig
from poodle.mutate import mutate_lines

if TYPE_CHECKING:
    from poodle.data_types import TestingResults


def report_summary(echo: Callable, testing_results: TestingResults, *_, **__) -> None:
    """Echo quick summary to console."""
    echo("")
    summary = testing_results.summary
    if summary.trials < 1:
        echo(click.style("!!! No mutants found to test !!!", fg="yellow"))
        return

    echo(click.style("*** Results Summary ***", fg="green"))
    echo(f"Testing found {summary.success_rate:.1%} of Mutants.")
    if summary.not_found:
        echo(f" - {summary.not_found} mutant(s) were not found.")
    if summary.timeout:
        echo(f" - {summary.timeout} mutant(s) caused trial to timeout.")
    if summary.errors:
        echo(f" - {summary.errors} mutant(s) could not be tested due to an error.")


display_reason_code = {
    MutantTrialResult.RC_FOUND: "FOUND",
    MutantTrialResult.RC_INCOMPLETE: "Testing Incomplete",
    MutantTrialResult.RC_NOT_FOUND: "Mutant Not Found",
    MutantTrialResult.RC_TIMEOUT: "Trial Exceeded Timeout",
}


def report_not_found(config: PoodleConfig, echo: Callable, testing_results: TestingResults, *_, **__) -> None:
    """Echo information about Trials that did not pass."""
    out_lines = []

    failed_trials = [trial for trial in testing_results.mutant_trials if not trial.result.passed]
    if not failed_trials:
        return

    failed_trials.sort(
        key=lambda trial: (
            trial.mutant.source_folder,
            str(trial.mutant.source_file) or "",
            trial.mutant.lineno,
            trial.mutant.mutator_name,
        )
    )

    out_lines.append("")
    out_lines.append(click.style("*** Mutants Not Found ***", fg="yellow"))
    for trial in failed_trials:
        mutant = trial.mutant
        result = trial.result

        out_lines.append("")
        out_lines.append(f"Mutant Trial Result: {display_reason_code.get(result.reason_code, result.reason_code)}")
        out_lines.append(f"Mutator: {mutant.mutator_name}")
        if result.reason_desc:
            out_lines.append(result.reason_desc)

        if mutant.source_file:
            file_lines = mutant.source_file.read_text("utf-8").splitlines(keepends=True)
            file_name = str(mutant.source_file.resolve())
            diff = list(
                difflib.unified_diff(
                    a=file_lines,
                    b=mutate_lines(mutant, file_lines),
                    fromfile=file_name,
                    tofile=f"[Mutant] {file_name}:{mutant.lineno}",
                )
            )

            out_lines.append("".join(diff))
        else:
            out_lines.append(
                f"source_file={mutant.source_file} lineno={mutant.lineno} col_offset={mutant.col_offset} "
                f"end_lineno={mutant.end_lineno} end_col_offset={mutant.end_col_offset}"
            )
            out_lines.append("text:")
            out_lines.append(mutant.text)

    not_found_file = config.reporter_opts.get("not_found_file")
    if not_found_file:
        Path(not_found_file).write_text("\n".join(out_lines))
    else:
        for line in out_lines:
            echo(line)
