"""Run mutation tests."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path
from subprocess import TimeoutExpired

from poodle.data_types import Mutant, MutantTrialResult, PoodleConfig
from poodle.util import pprint_str

logger = logging.getLogger(__name__)


def runner(
    config: PoodleConfig, run_folder: Path, mutant: Mutant, timeout: float | None, *_, **__
) -> MutantTrialResult:
    """Run test of mutant with command line command in subprocess."""
    logger.info("Running: run_folder=%s timeout=%s", run_folder, timeout)

    cwd = Path.cwd().resolve()
    run_cwd = run_folder.resolve() if mutant.source_folder.resolve() == cwd else cwd
    run_source_folder = run_folder.resolve() / mutant.source_folder

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
        "MUT_SOURCE_FILE": str(mutant.source_file),
        "MUT_LINENO": str(mutant.lineno),
        "MUT_END_LINENO": str(mutant.end_lineno),
        "MUT_COL_OFFSET": str(mutant.col_offset),
        "MUT_END_COL_OFFSET": str(mutant.end_col_offset),
        "MUT_TEXT": str(mutant.text),
    }
    if "command_line_env" in config.runner_opts:
        update_env.update(config.runner_opts["command_line_env"])
    run_env.update(update_env)

    logger.debug("update_env=%s", pprint_str(update_env))

    cmd: str = config.runner_opts.get("command_line", "pytest -x --assert=plain -o pythonpath='{PYTHONPATH}'")
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
        return MutantTrialResult(
            found=False,
            reason_code=MutantTrialResult.RC_TIMEOUT,
            reason_desc=f"TimeoutExpired {te}",
        )

    if result.returncode == 1:
        return MutantTrialResult(found=True, reason_code=MutantTrialResult.RC_FOUND)
    if result.returncode == 0:
        return MutantTrialResult(
            found=False,
            reason_code=MutantTrialResult.RC_NOT_FOUND,
        )
    return MutantTrialResult(
        found=True,
        reason_code=MutantTrialResult.RC_OTHER,
        reason_desc=result.stdout.decode("utf-8", errors="replace")  # nomut: String
        + "\n"
        + result.stderr.decode("utf-8", errors="replace"),  # nomut: String
    )
