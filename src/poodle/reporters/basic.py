from __future__ import annotations

from typing import Callable

from ..data_types import TestingResults


def report_summary(echo: Callable, testing_results: TestingResults, *_, **__) -> None:  # noqa: ARG001
    summary = testing_results.summary
    if summary.trials < 1:
        echo("No mutants found to test.")
        return

    echo("Results Summary")
    echo(f"Testing found {summary.success_rate:.1%} of Mutants")
    if summary.not_found:
        echo(f" - {summary.not_found} mutant(s) were not found")
    if summary.timeout:
        echo(f" - {summary.timeout} mutant(s) caused trial to timeout.")
    if summary.errors:
        echo(f" - {summary.errors} mutant(s) could not be tested due to an error.")


def report_not_found(echo: Callable, testing_results: TestingResults, *_, **__) -> None:  # noqa: ARG001
    failed_trials = [trial for trial in testing_results.mutant_trials if not trial.result.passed]
    if failed_trials:
        echo("\nMutants Not Found:")
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
