"""Basic Mutation Test Result Reporters."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from poodle.data_types import PoodleConfig, TestingResults
from poodle.util import to_json


def get_include_statuses(config: PoodleConfig, prefix: str) -> set[bool]:
    """Get set of statuses to include in report."""
    include_statuses = set()
    if config.reporter_opts.get(f"{prefix}_report_found", False):
        include_statuses.add(True)  # noqa: FBT003
    if config.reporter_opts.get(f"{prefix}_report_not_found", True):
        include_statuses.add(False)  # noqa: FBT003
    return include_statuses


def report_summary(echo: Callable, testing_results: TestingResults, *_, **__) -> None:
    """Echo quick summary to console."""
    echo("")
    summary = testing_results.summary
    if summary.trials < 1:
        echo("!!! No mutants found to test !!!", fg="yellow")
        return

    echo("*** Results Summary ***", fg="green")
    echo(f"Testing found {summary.success_rate:.1%} of Mutants.")
    if summary.not_found:
        echo(f" - {summary.not_found} mutant(s) were not found.")
    if summary.timeout:
        echo(f" - {summary.timeout} mutant(s) caused trial to timeout.")
    if summary.errors:
        echo(f" - {summary.errors} mutant(s) could not be tested due to an error.")


def report_not_found(config: PoodleConfig, echo: Callable, testing_results: TestingResults, *_, **__) -> None:
    """Echo information about Trials that did not pass."""
    failed_trials = [trial for trial in testing_results.mutant_trials if not trial.result.found]
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

    not_found_file = config.reporter_opts.get("not_found_file")

    echo("", file=not_found_file)
    echo("*** Mutants Not Found ***", fg="yellow", file=not_found_file)
    for trial in failed_trials:
        mutant = trial.mutant
        result = trial.result

        echo("", file=not_found_file)
        echo(
            f"Mutant Trial Result: {result.reason_code}",
            file=not_found_file,
        )
        echo(f"Mutator: {mutant.mutator_name}", file=not_found_file)
        if result.reason_desc:
            echo(result.reason_desc, file=not_found_file)

        if mutant.unified_diff:
            echo(mutant.unified_diff, file=not_found_file)
        else:
            echo(
                f"source_file={mutant.source_file} lineno={mutant.lineno} col_offset={mutant.col_offset} "
                f"end_lineno={mutant.end_lineno} end_col_offset={mutant.end_col_offset}",
                file=not_found_file,
            )
            echo("text:", file=not_found_file)
            echo(mutant.text, file=not_found_file)


def report_json(config: PoodleConfig, echo: Callable, testing_results: TestingResults, *_, **__) -> None:
    """Create JSON file with test results."""
    include_statuses = get_include_statuses(config, "json")
    mutant_trials = [trial for trial in testing_results.mutant_trials if trial.result.found in include_statuses]

    out_results = TestingResults(
        summary=testing_results.summary  # type: ignore [arg-type]
        if config.reporter_opts.get("json_include_summary", True)
        else None,
        mutant_trials=mutant_trials,
    )

    json_file = config.reporter_opts.get("json_report_file", "mutation-testing-report.json")
    if json_file == "sysout":
        echo(to_json(out_results, indent=4))
    else:
        Path(json_file).write_text(to_json(out_results))

    echo(f"JSON report written to {json_file!s}", fg="green")
