"""Run mutation tests."""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import TYPE_CHECKING

from poodle.data_types import Mutant, MutantTrialResult, PoodleConfig

if TYPE_CHECKING:
    from pathlib import Path


def runner(config: PoodleConfig, run_folder: Path, mutant: Mutant, *_, **__) -> MutantTrialResult:
    """Run test of mutant with command line command in subprocess."""
    run_env = os.environ.copy()
    python_path = os.pathsep.join(
        [
            str(run_folder.resolve() / mutant.source_folder),
            run_env.get("PYTHONPATH", ""),
        ],
    )
    run_env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": python_path,
            "MUT_SOURCE_FILE": str(mutant.source_file),
            "MUT_LINENO": str(mutant.lineno),
            "MUT_END_LINENO": str(mutant.end_lineno),
            "MUT_COL_OFFSET": str(mutant.col_offset),
            "MUT_END_COL_OFFSET": str(mutant.end_col_offset),
            "MUT_TEXT": str(mutant.text),
        },
    )
    if "command_line_env" in config.runner_opts:
        run_env.update(config.runner_opts["command_line_env"])

    result = subprocess.run(
        shlex.split(config.runner_opts["command_line"]),  # noqa: S603
        env=run_env,
        capture_output=True,
        check=False,
    )

    if result.returncode == 1:
        return MutantTrialResult(
            passed=True,
            reason_code=MutantTrialResult.RC_FOUND,
            reason_desc=result.stdout.decode("utf-8") + "\n" + result.stderr.decode("utf-8"),
        )
    if result.returncode == 0:
        return MutantTrialResult(
            passed=False,
            reason_code=MutantTrialResult.RC_NOT_FOUND,
        )
    return MutantTrialResult(
        passed=True,
        reason_code=MutantTrialResult.RC_OTHER,
        reason_desc=result.stdout.decode("utf-8") + "\n" + result.stderr.decode("utf-8"),
    )
