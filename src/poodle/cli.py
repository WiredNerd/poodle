from __future__ import annotations

import sys
from pathlib import Path

import click
from click import Context

from . import core
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
# @click.option("-P", "--max_parallel", type=int, help="Maximum number of parallel runners.")
# @click.option("-F", "--folder-prefix", help="Prefix for runner folder names")
# @click.option("-R", "--runner", help="Runner Name or Module Name for runner to use")
def main(source: tuple[Path], config_file: Path | None, verbosity: str | None):
    """Run Mutation testing"""
    try:
        config = build_config(source, config_file, verbosity)
    except ValueError as ve:
        click.echo(ve.args)
        sys.exit(4)

    core.run(config)


# Exit code 0: All tests were collected and passed successfully
# Exit code 1: Tests were collected and run but some of the tests failed
# Exit code 2: Test execution was interrupted by the user
# Exit code 3: Internal error happened while executing tests
# Exit code 4: pytest command line usage error
# Exit code 5: No tests were collected

if __name__ == "__main__":
    main()
