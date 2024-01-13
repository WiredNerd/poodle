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
from .common.base import poodle_config
from .common.config import PoodleConfigData
from .config import build_config
from .plugins import (
    click_epilog_from_plugins,
    click_options_from_plugins,
    collect_options,
    plugin_manager,
    register_plugins,
)

register_plugins()


CONTEXT_SETTINGS = {
    "max_content_width": 120,
}

collect_options()


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True, epilog=click_epilog_from_plugins())
@click.argument("sources", type=click.Path(exists=True, path_type=Path), nargs=-1)
@click.option("-c", "config_file", help="Configuration File.", type=click.Path(exists=True, path_type=Path))
@click.option("-q", "quiet", help="Quiet mode: q, qq, or qqq", count=True)
@click.option("-v", "verbose", help="Verbose mode: v, vv, or vvv", count=True)
@click.option("-w", "workers", help="Maximum number of parallel workers.", type=int)
@click.option("--exclude", help="Add a glob exclude file filter. Multiple allowed.", multiple=True)
@click.option("--only", help="Glob pattern for files to mutate. Multiple allowed.", multiple=True)
@click.option("--report", help="Enable reporter by name. Multiple allowed.", multiple=True)
@click_options_from_plugins()
@click.option("--fail_under", help="Fail if mutation score is under this value.", type=float)
@click.version_option(version=__version__)
def main(**cmd_kwargs: dict) -> None:
    """Poodle Mutation Test Tool."""
    try:
        config_data = PoodleConfigData(cmd_kwargs)
        config = build_config(
            cmd_sources=cmd_kwargs["sources"],
            cmd_config_file=cmd_kwargs["config_file"],
            cmd_quiet=cmd_kwargs["quiet"],
            cmd_verbose=cmd_kwargs["verbose"],
            cmd_max_workers=cmd_kwargs["workers"],
            cmd_excludes=cmd_kwargs["exclude"],
            cmd_only_files=cmd_kwargs["only"],
            cmd_report=cmd_kwargs["report"],
            cmd_html=cmd_kwargs["html"],
            cmd_json=cmd_kwargs["json"],
            cmd_fail_under=cmd_kwargs["fail_under"],
        )
    except PoodleInputError as err:
        for arg in err.args:
            click.secho(arg, fg="red")
        sys.exit(4)

    try:
        plugin_manager.hook.configure(config=config_data, poodle_config=poodle_config, cmd_kwargs=cmd_kwargs)
        core.main_process(config, config_data)
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
