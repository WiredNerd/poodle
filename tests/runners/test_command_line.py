# import os
# from pathlib import Path
# from subprocess import CompletedProcess, TimeoutExpired
# from unittest import mock

# import pytest

# from poodle.common import Mutant, MutantTrialResult
# from poodle.runners import command_line
# from poodle.common.util import pprint_str


# @pytest.fixture()
# def subprocess_run():
#     with mock.patch("subprocess.run") as subprocess_run:
#         yield subprocess_run


# @pytest.fixture()
# def logger_mock():
#     with mock.patch("poodle.runners.command_line.logger") as logger_mock:
#         yield logger_mock


# def test_logger():
#     assert command_line.logger.name == "poodle.runners.command_line"


# class TestCommandLineRunner:
#     def test_runner(self, subprocess_run, logger_mock):
#         with mock.patch.dict("os.environ", {"PYTHONPATH": "/project/src"}, clear=True):
#             subprocess_run.return_value = CompletedProcess(
#                 args="",
#                 returncode=1,
#                 stdout=b"output",
#                 stderr=b"error",
#             )

#             config = mock.MagicMock()
#             config.runner_opts = {
#                 "command_line_env": {"CUSTOM_FIELD": "VALUE1"},
#             }

#             mutant = Mutant(
#                 mutator_name="test",
#                 source_folder=Path("src"),
#                 source_file=Path("target.py"),
#                 lineno=1,
#                 col_offset=2,
#                 end_lineno=3,
#                 end_col_offset=4,
#                 text="Changed Line",
#             )

#             out = command_line.runner(
#                 config=config,
#                 run_folder=Path("poodle-run-folder"),
#                 mutant=mutant,
#                 timeout=1,
#                 other="value",
#             )

#             logger_mock.info.assert_any_call("Running: run_folder=%s timeout=%s", Path("poodle-run-folder"), 1)

#             python_path = os.pathsep.join(
#                 [
#                     str(Path("poodle-run-folder").resolve() / Path("src")),
#                     str(Path.cwd().resolve()),
#                     "/project/src",
#                 ],
#             )

#             update_env = {
#                 "PYTHONDONTWRITEBYTECODE": "1",
#                 "PYTHONPATH": python_path,
#                 "MUT_SOURCE_FILE": "target.py",
#                 "MUT_LINENO": "1",
#                 "MUT_COL_OFFSET": "2",
#                 "MUT_END_LINENO": "3",
#                 "MUT_END_COL_OFFSET": "4",
#                 "MUT_TEXT": "Changed Line",
#                 "CUSTOM_FIELD": "VALUE1",
#             }

#             subprocess_run.assert_called_with(
#                 ["pytest", "-x", "--assert=plain", "-o", f"pythonpath={python_path}"],
#                 cwd=Path.cwd().resolve(),
#                 env=update_env,
#                 capture_output=True,
#                 check=False,
#                 timeout=1,
#             )

#             logger_mock.debug.assert_any_call("update_env=%s", pprint_str(update_env))

#             logger_mock.debug.assert_any_call("command: %s", f"pytest -x --assert=plain -o pythonpath='{python_path}'")

#             assert out.found is True
#             assert out.reason_code == out.RC_FOUND
#             assert out.reason_desc is None

#     def test_runner_src_is_cwd(self, subprocess_run, logger_mock):
#         with mock.patch.dict("os.environ", {"PYTHONPATH": "/project/src"}, clear=True):
#             subprocess_run.return_value = CompletedProcess(
#                 args="",
#                 returncode=1,
#                 stdout=b"output",
#                 stderr=b"error",
#             )

#             config = mock.MagicMock()
#             config.runner_opts = {
#                 "command_line_env": {"CUSTOM_FIELD": "VALUE1"},
#             }

#             mutant = Mutant(
#                 mutator_name="test",
#                 source_folder=Path("."),  # noqa: PTH201
#                 source_file=Path("target.py"),
#                 lineno=1,
#                 col_offset=2,
#                 end_lineno=3,
#                 end_col_offset=4,
#                 text="Changed Line",
#             )

#             out = command_line.runner(
#                 config=config,
#                 run_folder=Path("poodle-run-folder"),
#                 mutant=mutant,
#                 timeout=1,
#                 other="value",
#             )

#             logger_mock.info.assert_any_call("Running: run_folder=%s timeout=%s", Path("poodle-run-folder"), 1)

#             python_path = os.pathsep.join(
#                 [
#                     str(Path("poodle-run-folder").resolve()),
#                     str(Path.cwd().resolve()),
#                     "/project/src",
#                 ],
#             )

#             update_env = {
#                 "PYTHONDONTWRITEBYTECODE": "1",
#                 "PYTHONPATH": python_path,
#                 "MUT_SOURCE_FILE": "target.py",
#                 "MUT_LINENO": "1",
#                 "MUT_COL_OFFSET": "2",
#                 "MUT_END_LINENO": "3",
#                 "MUT_END_COL_OFFSET": "4",
#                 "MUT_TEXT": "Changed Line",
#                 "CUSTOM_FIELD": "VALUE1",
#             }

#             subprocess_run.assert_called_with(
#                 ["pytest", "-x", "--assert=plain", "-o", f"pythonpath={python_path}"],
#                 cwd=Path("poodle-run-folder").resolve(),
#                 env=update_env,
#                 capture_output=True,
#                 check=False,
#                 timeout=1,
#             )

#             logger_mock.debug.assert_any_call("update_env=%s", pprint_str(update_env))

#             logger_mock.debug.assert_any_call("command: %s", f"pytest -x --assert=plain -o pythonpath='{python_path}'")

#             assert out.found is True
#             assert out.reason_code == out.RC_FOUND
#             assert out.reason_desc is None

#     def test_unset_path(self, subprocess_run):
#         with mock.patch.dict("os.environ", {}, clear=True):
#             subprocess_run.return_value = CompletedProcess(
#                 args="",
#                 returncode=1,
#                 stdout=b"output",
#                 stderr=b"error",
#             )

#             config = mock.MagicMock()
#             config.runner_opts = {"command_line": "pytest tests"}

#             mutant = Mutant(
#                 mutator_name="test",
#                 source_folder=Path("src"),
#                 source_file=Path("target.py"),
#                 lineno=1,
#                 col_offset=2,
#                 end_lineno=3,
#                 end_col_offset=4,
#                 text="Changed Line",
#             )

#             python_path = os.pathsep.join(
#                 [
#                     str(Path("poodle-run-folder").resolve() / Path("src")),
#                     str(Path.cwd().resolve()),
#                     "",
#                 ],
#             )

#             out = command_line.runner(
#                 config=config,
#                 run_folder=Path("poodle-run-folder"),
#                 mutant=mutant,
#                 timeout=1,
#             )

#             subprocess_run.assert_called_with(
#                 ["pytest", "tests"],
#                 cwd=Path.cwd().resolve(),
#                 env={
#                     "PYTHONDONTWRITEBYTECODE": "1",
#                     "PYTHONPATH": python_path,
#                     "MUT_SOURCE_FILE": "target.py",
#                     "MUT_LINENO": "1",
#                     "MUT_COL_OFFSET": "2",
#                     "MUT_END_LINENO": "3",
#                     "MUT_END_COL_OFFSET": "4",
#                     "MUT_TEXT": "Changed Line",
#                 },
#                 capture_output=True,
#                 check=False,
#                 timeout=1,
#             )

#             assert out.found is True
#             assert out.reason_code == out.RC_FOUND
#             assert out.reason_desc is None

#     def test_rc_0(self, subprocess_run):
#         with mock.patch.dict("os.environ", {}, clear=True):
#             subprocess_run.return_value = CompletedProcess(
#                 args="",
#                 returncode=0,
#                 stdout=b"output",
#                 stderr=b"error",
#             )

#             config = mock.MagicMock()
#             config.runner_opts = {"command_line": "pytest tests"}

#             python_path = os.pathsep.join(
#                 [
#                     str(Path("poodle-run-folder").resolve() / Path("src")),
#                     str(Path.cwd().resolve()),
#                     "",
#                 ],
#             )

#             mutant = Mutant(
#                 mutator_name="test",
#                 source_folder=Path("src"),
#                 source_file=Path("target.py"),
#                 lineno=1,
#                 col_offset=2,
#                 end_lineno=3,
#                 end_col_offset=4,
#                 text="Changed Line",
#             )

#             out = command_line.runner(
#                 config=config,
#                 run_folder=Path("poodle-run-folder"),
#                 mutant=mutant,
#                 timeout=1,
#             )

#             subprocess_run.assert_called_with(
#                 ["pytest", "tests"],
#                 cwd=Path.cwd().resolve(),
#                 env={
#                     "PYTHONDONTWRITEBYTECODE": "1",
#                     "PYTHONPATH": python_path,
#                     "MUT_SOURCE_FILE": "target.py",
#                     "MUT_LINENO": "1",
#                     "MUT_COL_OFFSET": "2",
#                     "MUT_END_LINENO": "3",
#                     "MUT_END_COL_OFFSET": "4",
#                     "MUT_TEXT": "Changed Line",
#                 },
#                 capture_output=True,
#                 check=False,
#                 timeout=1,
#             )

#             assert out.found is False
#             assert out.reason_code == out.RC_NOT_FOUND
#             assert out.reason_desc is None

#     def test_rc_2(self, subprocess_run):
#         with mock.patch.dict("os.environ", {}, clear=True):
#             subprocess_run.return_value = CompletedProcess(
#                 args="",
#                 returncode=2,
#                 stdout=b"output",
#                 stderr=b"error",
#             )

#             config = mock.MagicMock()
#             config.runner_opts = {"command_line": "pytest tests"}

#             python_path = os.pathsep.join(
#                 [
#                     str(Path("poodle-run-folder").resolve() / Path("src")),
#                     str(Path.cwd().resolve()),
#                     "",
#                 ],
#             )

#             mutant = Mutant(
#                 mutator_name="test",
#                 source_folder=Path("src"),
#                 source_file=Path("target.py"),
#                 lineno=1,
#                 col_offset=2,
#                 end_lineno=3,
#                 end_col_offset=4,
#                 text="Changed Line",
#             )

#             out = command_line.runner(
#                 config=config,
#                 run_folder=Path("poodle-run-folder"),
#                 mutant=mutant,
#                 timeout=1,
#             )

#             subprocess_run.assert_called_with(
#                 ["pytest", "tests"],
#                 cwd=Path.cwd().resolve(),
#                 env={
#                     "PYTHONDONTWRITEBYTECODE": "1",
#                     "PYTHONPATH": python_path,
#                     "MUT_SOURCE_FILE": "target.py",
#                     "MUT_LINENO": "1",
#                     "MUT_COL_OFFSET": "2",
#                     "MUT_END_LINENO": "3",
#                     "MUT_END_COL_OFFSET": "4",
#                     "MUT_TEXT": "Changed Line",
#                 },
#                 capture_output=True,
#                 check=False,
#                 timeout=1,
#             )

#             assert out.found is True
#             assert out.reason_code == out.RC_OTHER
#             assert out.reason_desc == "output\nerror"

#     def test_timeout(self, subprocess_run):
#         with mock.patch.dict("os.environ", {}, clear=True):
#             subprocess_run.side_effect = TimeoutExpired(cmd="pytest tests", timeout=10.0, output="running pytest")

#             config = mock.MagicMock()
#             config.runner_opts = {"command_line": "pytest tests"}

#             mutant = Mutant(
#                 mutator_name="test",
#                 source_folder=Path("src"),
#                 source_file=Path("target.py"),
#                 lineno=1,
#                 col_offset=2,
#                 end_lineno=3,
#                 end_col_offset=4,
#                 text="Changed Line",
#             )

#             out = command_line.runner(
#                 config=config,
#                 run_folder=Path("poodle-run-folder"),
#                 mutant=mutant,
#                 timeout=10.0,
#             )

#             assert out.found is False
#             assert out.reason_code == MutantTrialResult.RC_TIMEOUT
#             assert out.reason_desc == "TimeoutExpired Command 'pytest tests' timed out after 10.0 seconds"
