"""Command Line Interface."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import PoodleInputError, core
from .config import build_config

CONTEXT_SETTINGS = {
    "max_content_width": 200,
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("source", type=click.Path(exists=True, path_type=Path), nargs=-1)
@click.option("-C", "--config_file", help="Configuration File.", type=click.Path(exists=True, path_type=Path))
@click.option("-q", "verbosity", help="Quiet mode: disabled normal output, and loglevel=ERROR", flag_value="q")
@click.option("-v", "verbosity", help="Verbose mode: loglevel=INFO", flag_value="v")
@click.option("-vv", "verbosity", help="Very Verbose mode: loglevel=DEBUG", flag_value="vv")
@click.option("-P", "--max_workers", type=int, help="Maximum number of parallel workers.")
@click.option(
    "--exclude", "excludes", multiple=True, help="Add a regex filter for which files NOT to mutate.  Multiple allowed."
)
@click.option(
    "--only",
    "only_files",
    multiple=True,
    help="Glob pattern for files to mutate.  If specified, no other files will be mutated.  Multiple allowed.",
)
# @click.option("-R", "--runner", help="Runner Name or Module Name for runner to use")
def main(
    source: tuple[Path],
    config_file: Path | None,
    verbosity: str | None,
    max_workers: int | None,
    excludes: tuple[str],
    only_files: tuple[str],
) -> None:
    """Poodle Mutation Test Tool."""
    try:
        config = build_config(source, config_file, verbosity, max_workers, excludes, only_files)
    except PoodleInputError as err:
        click.echo(err.args)
        sys.exit(4)

    try:
        core.main(config)
    except KeyboardInterrupt:
        click.echo("Aborted due to Keyboard Interrupt!")
        sys.exit(2)


# pytest return codes
# Exit code 0: All tests were collected and passed successfully
# Exit code 1: Tests were collected and run but some of the tests failed
# Exit code 2: Test execution was interrupted by the user
# Exit code 3: Internal error happened while executing tests
# Exit code 4: pytest command line usage error
# Exit code 5: No tests were collected

if __name__ == "__main__":
    main()
