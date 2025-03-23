"""Command Line Interface."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import click

from . import (
    PoodleInputError,
    PoodleNoMutantsFoundError,
    PoodleTestingFailedError,
    PoodleTrialRunError,
    __version__,
    core,
)
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
@click.option("--html", help="Folder name to store HTML report in.", type=click.Path(path_type=Path))
@click.option("--json", help="File to create with JSON report.", type=click.Path(path_type=Path))
@click.option("--fail_under", help="Fail if mutation score is under this value.", type=float)
@click.version_option(version=__version__)
def main(  # noqa: C901, PLR0912
    sources: tuple[Path],
    config_file: Path | None,
    quiet: int,
    verbose: int,
    workers: int | None,
    exclude: tuple[str],
    only: tuple[str],
    report: tuple[str],
    html: Path | None,
    json: Path | None,
    fail_under: float | None,
) -> None:
    """Poodle Mutation Test Tool."""
    try:
        config = build_config(
            sources, config_file, quiet, verbose, workers, exclude, only, report, html, json, fail_under
        )
    except PoodleInputError as err:
        for arg in err.args:
            click.secho(arg, fg="red")
        sys.exit(4)

    try:
        core.main_process(config)
    except PoodleTestingFailedError as err:
        for arg in err.args:
            click.secho(arg, fg="yellow")
        sys.exit(1)
    except KeyboardInterrupt:
        click.secho("Aborted due to Keyboard Interrupt!", fg="yellow")
        sys.exit(2)
    except PoodleTrialRunError as err:
        for arg in err.args:
            click.secho(arg, fg="red")
        sys.exit(3)
    except PoodleInputError as err:
        for arg in err.args:
            click.secho(arg, fg="red")
        sys.exit(4)
    except PoodleNoMutantsFoundError as err:
        for arg in err.args:
            click.secho(arg, fg="yellow")
        sys.exit(5)
    except:  # noqa: E722
        click.secho("Aborted due to Internal Error!", fg="red")
        click.secho(traceback.format_exc(), fg="red")
        sys.exit(3)
    sys.exit(0)


# nomut: start
if __name__ == "__main__":
    main()
