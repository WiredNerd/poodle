"""Command Line Interface."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import click

from . import PoodleInputError, core
from .config import build_config

CONTEXT_SETTINGS = {
    "max_content_width": 120,
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("sources", type=click.Path(exists=True, path_type=Path), nargs=-1)
@click.option("-c", "config_file", help="Configuration File.", type=click.Path(exists=True, path_type=Path))
@click.option("-q", "quiet", help="Quiet mode: q, qq, or qqq", count=True)
@click.option("-v", "verbose", help="Verbose mode: v, vv, or vvv", count=True)
@click.option("-w", "workers", help="Maximum number of parallel workers.", type=int)
@click.option("--exclude", help="Add a glob exclude file filter. Multiple allowed.", multiple=True)
@click.option("--only", help="Glob pattern for files to mutate. Multiple allowed.", multiple=True)
@click.option("--report", help="Enable reporter by name. Multiple allowed.", multiple=True)
def main(
    sources: tuple[Path],
    config_file: Path | None,
    quiet: int,
    verbose: int,
    workers: int | None,
    exclude: tuple[str],
    only: tuple[str],
    report: tuple[str],
) -> None:
    """Poodle Mutation Test Tool."""
    try:
        config = build_config(sources, config_file, quiet, verbose, workers, exclude, only, report)
    except PoodleInputError as err:
        click.echo(err.args)
        sys.exit(4)

    try:
        core.main_process(config)
    except KeyboardInterrupt:
        click.echo("Aborted due to Keyboard Interrupt!")
        sys.exit(2)
    except:  # noqa: E722
        click.echo("Aborted due to Internal Error!")
        click.echo(traceback.format_exc())
        sys.exit(3)
    sys.exit(0)


# pytest return codes
# Exit code 0: All tests were collected and passed successfully
# Exit code 1: Tests were collected and run but some of the tests failed
# Exit code 2: Test execution was interrupted by the user
# Exit code 3: Internal error happened while executing tests
# Exit code 4: pytest command line usage error
# Exit code 5: No tests were collected


# nomut: start
if __name__ == "__main__":
    main()
