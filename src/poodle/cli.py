import sys

import click
from click import echo

from poodle import core
from poodle.config import build_config


@click.command()
@click.argument("source", type=click.Path(exists=True), nargs=-1)
@click.option("-C", "--config_file", help="Configuration File.")
# @click.option("-P", "--max_parallel", type=int, help="Maximum number of parallel runners.")
# @click.option("-F", "--folder-prefix", help="Prefix for runner folder names")
# @click.option("-R", "--runner", help="Runner Name or Module Name for runner to use")
def main(source, config_file):
    """Run Mutation testing"""
    try:
        config = build_config(source, config_file)
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
