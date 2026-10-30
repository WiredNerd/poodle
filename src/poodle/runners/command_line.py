"""Run mutation tests."""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from subprocess import TimeoutExpired

from poodle import PoodleInputError
from poodle.data_types import Mutant, MutantTrialResult, PoodleConfig
from poodle.util import pprint_str

logger = logging.getLogger(__name__)


def runner(
    config: PoodleConfig, run_folder: Path, mutant: Mutant, timeout: float | None, *_, **__
) -> MutantTrialResult:
    """Run test of mutant with command line command in subprocess."""
    output_dir = validate_output_dir(config)
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

    paths = None
    if output_dir is not None:
        result, paths = run_with_output(output_dir, shlex.split(cmd), run_cwd, run_env, mutant, timeout)
    else:
        try:
            result = subprocess.run(  # noqa: S603
                shlex.split(cmd),
                cwd=run_cwd,
                env=run_env,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except TimeoutExpired as error:
            result = error

    if isinstance(result, TimeoutExpired):
        description = f"TimeoutExpired {result}"
        if paths:
            description += f"\n{paths}"
        return MutantTrialResult(
            found=False,
            reason_code=MutantTrialResult.RC_TIMEOUT,
            reason_desc=description,
        )
    if result.returncode == 1:
        return MutantTrialResult(found=True, reason_code=MutantTrialResult.RC_FOUND, reason_desc=paths)
    if result.returncode == 0:
        return MutantTrialResult(found=False, reason_code=MutantTrialResult.RC_NOT_FOUND, reason_desc=paths)
    return MutantTrialResult(
        found=True,
        reason_code=MutantTrialResult.RC_OTHER,
        reason_desc=paths
        if paths is not None
        else result.stdout.decode("utf-8", errors="replace")  # nomut: String
        + "\n"
        + result.stderr.decode("utf-8", errors="replace"),  # nomut: String
    )


def validate_output_dir(config: PoodleConfig) -> Path | None:
    """Keep retained output outside folders that are copied or removed."""
    value = config.runner_opts.get("output_dir")
    if value is None:
        return None
    if not isinstance(value, (str, Path)) or not str(value):
        raise PoodleInputError("runner_opts.output_dir must be a nonempty string or Path")
    output_dir = Path(value).resolve()
    protected = [config.work_folder, *config.source_folders]
    if any(output_dir.is_relative_to(folder.resolve()) for folder in protected):
        raise PoodleInputError("runner_opts.output_dir must be outside work_folder and all source_folders")
    return output_dir


def run_with_output(  # noqa: PLR0913, PLR0917
    output_dir: Path,
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    mutant: Mutant,
    timeout: float | None,
) -> tuple[subprocess.CompletedProcess[bytes] | TimeoutExpired, str]:
    """Stream command bytes into retained files and record the process outcome."""
    output_dir.mkdir(parents=True, exist_ok=True)
    trial_dir = Path(tempfile.mkdtemp(prefix="trial-", dir=output_dir))
    stdout_path = trial_dir / "stdout.txt"
    stderr_path = trial_dir / "stderr.txt"
    receipt_path = trial_dir / "trial.json"
    paths = f"Receipt: {receipt_path}\nStdout: {stdout_path}\nStderr: {stderr_path}"
    status = "interrupted"
    return_code: int | None = None
    try:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            try:
                process = subprocess.run(  # noqa: S603
                    command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, check=False, timeout=timeout
                )
            except TimeoutExpired as error:
                status = "timeout"
                process = error
            else:
                status = "completed"
                return_code = process.returncode
    except BaseException as error:
        status = "launch_error" if isinstance(error, OSError) else "interrupted"
        try:
            write_output_receipt(receipt_path, mutant, status, return_code)
        except OSError:
            logger.exception("Could not write output receipt after command failure")
        raise
    write_output_receipt(receipt_path, mutant, status, return_code)
    return process, paths


def write_output_receipt(path: Path, mutant: Mutant, status: str, return_code: int | None) -> None:
    """Write mutation identity and process status beside retained command output."""
    metadata = {"mutant": mutant.to_dict(), "status": status, "return_code": return_code}
    path.write_text(json.dumps(metadata, ensure_ascii=True), encoding="utf-8")
