"""Run mutation tests."""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import TYPE_CHECKING

from poodle.data import PoodleConfig, PoodleTestResult, SourceFileMutant

if TYPE_CHECKING:
    from pathlib import Path

"""
runner(config: PoodleConfig, run_folder: Path, mutant: PoodleMutant, **_) -> PoodleTestResult:
"""


def command_line_runner(config: PoodleConfig, run_folder: Path, mutant: SourceFileMutant, **_) -> PoodleTestResult:
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

    result = subprocess.run(
        shlex.split(config.runner_opts["command_line"]),  # noqa: S603
        env=run_env,
        capture_output=True,
        check=True,
    )

    if result.returncode == 1:
        return PoodleTestResult(
            test_passed=True,
            reason_code=PoodleTestResult.RC_FOUND,
            reason_desc=result.stderr.decode("utf-8"),
        )
    if result.returncode == 0:
        return PoodleTestResult(
            test_passed=False,
            reason_code=PoodleTestResult.RC_NOT_FOUND,
        )
    return PoodleTestResult(
        test_passed=True,
        reason_code=PoodleTestResult.RC_OTHER,
        reason_desc=result.stderr.decode("utf-8"),
    )
