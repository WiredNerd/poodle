"""Run mutation tests."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path
from subprocess import TimeoutExpired

import pluggy

from poodle import Mutant, PoodleConfigData, RunResult
from poodle.common.util import pprint_to_str

hookimpl = pluggy.HookimplMarker("poodle")


logger = logging.getLogger(__name__)


@hookimpl(specname="run_testing")
def command_line_runner(
    run_folder: Path,
    timeout: float | None,
    config: PoodleConfigData,
    source_folder: Path,
    mutant: Mutant | None,
) -> RunResult | None:
    """Run test of clean source with command line command in subprocess."""
    if not config.runner == "command_line":
        return

    logger.info("Running: run_folder=%s timeout=%s", run_folder, timeout)

    runner_opts = config.merge_dict_from_config(
        "command_line_runner",
        {
            "command": "pytest -x --assert=plain -o pythonpath='{PYTHONPATH}'",
        },
    )

    cwd = Path.cwd().resolve()
    run_cwd = run_folder.resolve() if source_folder.resolve() == cwd else cwd
    run_source_folder = run_folder.resolve() / source_folder

    run_env = os.environ.copy()
    python_path = os.pathsep.join(
        [
            str(run_source_folder),
            str(Path.cwd().resolve()),
            run_env.get("PYTHONPATH", ""),
        ],
    )
    update_env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": python_path,
    }
    if mutant:
        update_env.update(
            {
                "MUT_SOURCE_FILE": str(mutant.source_file),
                "MUT_LINENO": str(mutant.lineno),
                "MUT_END_LINENO": str(mutant.end_lineno),
                "MUT_COL_OFFSET": str(mutant.col_offset),
                "MUT_END_COL_OFFSET": str(mutant.end_col_offset),
                "MUT_TEXT": str(mutant.text),
            }
        )

    update_env.update(runner_opts.get("environment", {}))
    run_env.update(update_env)

    logger.debug("update_env=%s", pprint_to_str(update_env))

    cmd: str = runner_opts["command"]
    cmd = cmd.format(PYTHONPATH=python_path)
    logger.debug("command: %s", cmd)

    try:
        result = subprocess.run(
            shlex.split(cmd),  # noqa: S603
            cwd=run_cwd,
            env=run_env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except TimeoutExpired as te:
        return RunResult(
            result=RunResult.RESULT_TIMEOUT,
            description=f"TimeoutExpired {te}",
        )

    def capture_output(result: subprocess.CompletedProcess) -> str:
        """Capture output from completed process."""
        return (
            result.stdout.decode("utf-8", errors="replace")  # nomut: String
            + "\n"
            + result.stderr.decode("utf-8", errors="replace")  # nomut: String
        )

    if result.returncode == 0:
        return RunResult(
            result=RunResult.RESULT_PASSED,
            description=capture_output(result),
        )
    if result.returncode == 1:
        return RunResult(
            result=RunResult.RESULT_FAILED,
            description=capture_output(result),
        )
    return RunResult(
        result=RunResult.RESULT_ERROR,
        description=capture_output(result),
    )
