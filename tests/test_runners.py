import os
from pathlib import Path
from subprocess import CompletedProcess
from unittest import mock

import pytest

from poodle import runners
from poodle.data import PoodleMutant


@pytest.fixture()
def subprocess_run():
    with mock.patch("subprocess.run") as subprocess_run:
        yield subprocess_run


class TestCommandLineRunner:
    def test_command_line_runner(self, subprocess_run):
        with mock.patch.dict("os.environ", {"PYTHONPATH": "/project/src"}, clear=True):
            os.pathsep = ";"
            subprocess_run.return_value = CompletedProcess(
                args="",
                returncode=1,
                stdout="output",
                stderr="error",
            )

            config = mock.MagicMock()
            config.runner_opts = {"command_line": "pytest tests"}

            mutant = PoodleMutant(Path("src"), Path("target.py"), 1, 2, 3, 4, "Changed Line")

            out = runners.command_line_runner(
                config=config,
                run_folder=Path("poodle-run-folder"),
                mutant=mutant,
                other="value",
            )

            python_path = ";".join(
                [
                    str(Path("poodle-run-folder").resolve() / Path("src")),
                    "/project/src",
                ]
            )

            subprocess_run.assert_called_with(
                ["pytest", "tests"],
                env={
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": python_path,
                    "MUT_SOURCE_FILE": "target.py",
                    "MUT_LINENO": "1",
                    "MUT_COL_OFFSET": "2",
                    "MUT_END_LINENO": "3",
                    "MUT_END_COL_OFFSET": "4",
                    "MUT_TEXT": "Changed Line",
                },
                capture_output=True,
            )

            assert out.test_passed is True
            assert out.reason_code == out.RC_FOUND
            assert out.reason_desc == "error"

    def test_command_line_runner_unset_path(self, subprocess_run):
        with mock.patch.dict("os.environ", {}, clear=True):
            os.pathsep = ";"
            subprocess_run.return_value = CompletedProcess(
                args="",
                returncode=1,
                stdout="output",
                stderr="error",
            )

            config = mock.MagicMock()
            config.runner_opts = {"command_line": "pytest tests"}

            mutant = PoodleMutant(Path("src"), Path("target.py"), 1, 2, 3, 4, "Changed Line")

            out = runners.command_line_runner(
                config=config,
                run_folder=Path("poodle-run-folder"),
                mutant=mutant,
            )

            subprocess_run.assert_called_with(
                ["pytest", "tests"],
                env={
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(Path("poodle-run-folder").resolve() / Path("src")) + ";",
                    "MUT_SOURCE_FILE": "target.py",
                    "MUT_LINENO": "1",
                    "MUT_COL_OFFSET": "2",
                    "MUT_END_LINENO": "3",
                    "MUT_END_COL_OFFSET": "4",
                    "MUT_TEXT": "Changed Line",
                },
                capture_output=True,
            )

            assert out.test_passed is True
            assert out.reason_code == out.RC_FOUND
            assert out.reason_desc == "error"

    def test_command_line_runner_rc_0(self, subprocess_run):
        with mock.patch.dict("os.environ", {}, clear=True):
            os.pathsep = ";"
            subprocess_run.return_value = CompletedProcess(
                args="",
                returncode=0,
                stdout="output",
                stderr="error",
            )

            config = mock.MagicMock()
            config.runner_opts = {"command_line": "pytest tests"}

            mutant = PoodleMutant(Path("src"), Path("target.py"), 1, 2, 3, 4, "Changed Line")

            out = runners.command_line_runner(
                config=config,
                run_folder=Path("poodle-run-folder"),
                mutant=mutant,
            )

            subprocess_run.assert_called_with(
                ["pytest", "tests"],
                env={
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(Path("poodle-run-folder").resolve() / Path("src")) + ";",
                    "MUT_SOURCE_FILE": "target.py",
                    "MUT_LINENO": "1",
                    "MUT_COL_OFFSET": "2",
                    "MUT_END_LINENO": "3",
                    "MUT_END_COL_OFFSET": "4",
                    "MUT_TEXT": "Changed Line",
                },
                capture_output=True,
            )

            assert out.test_passed is False
            assert out.reason_code == out.RC_NOT_FOUND
            assert out.reason_desc is None

    def test_command_line_runner_rc_2(self, subprocess_run):
        with mock.patch.dict("os.environ", {}, clear=True):
            os.pathsep = ";"
            subprocess_run.return_value = CompletedProcess(
                args="",
                returncode=2,
                stdout="output",
                stderr="error",
            )

            config = mock.MagicMock()
            config.runner_opts = {"command_line": "pytest tests"}

            mutant = PoodleMutant(Path("src"), Path("target.py"), 1, 2, 3, 4, "Changed Line")

            out = runners.command_line_runner(
                config=config,
                run_folder=Path("poodle-run-folder"),
                mutant=mutant,
            )

            subprocess_run.assert_called_with(
                ["pytest", "tests"],
                env={
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(Path("poodle-run-folder").resolve() / Path("src")) + ";",
                    "MUT_SOURCE_FILE": "target.py",
                    "MUT_LINENO": "1",
                    "MUT_COL_OFFSET": "2",
                    "MUT_END_LINENO": "3",
                    "MUT_END_COL_OFFSET": "4",
                    "MUT_TEXT": "Changed Line",
                },
                capture_output=True,
            )

            assert out.test_passed is True
            assert out.reason_code == out.RC_OTHER
            assert out.reason_desc == "error"
