from unittest import mock

import pytest

from poodle import PoodleInputError, PoodleTrialRunError, core
from poodle.data_types import MutantTrial, PoodleWork
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def logger_mock():
    with mock.patch("poodle.core.logger") as logger_mock:
        yield logger_mock


def test_logger():
    assert core.logger.name == "poodle.core"


class TestMain:
    @mock.patch("poodle.core.PoodleWork")
    @mock.patch("poodle.core.pprint_str")
    @mock.patch("poodle.core.shutil")
    @mock.patch("poodle.core.create_temp_zips")
    @mock.patch("poodle.core.initialize_mutators")
    @mock.patch("poodle.core.get_runner")
    @mock.patch("poodle.core.generate_reporters")
    @mock.patch("poodle.core.create_mutants_for_all_mutators")
    @mock.patch("poodle.core.clean_run_each_source_folder")
    @mock.patch("poodle.core.run_mutant_trails")
    @mock.patch("poodle.core.click")
    @mock.patch("poodle.core.print_header")
    def test_main(
        self,
        print_header: mock.MagicMock,
        core_click: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
        clean_run_each_source_folder: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
        generate_reporters: mock.MagicMock,
        get_runner: mock.MagicMock,
        initialize_mutators: mock.MagicMock,
        create_temp_zips: mock.MagicMock,
        shutil: mock.MagicMock,
        pprint_str: mock.MagicMock,
        poodle_work_class: mock.MagicMock,
        logger_mock: mock.MagicMock,
    ):
        work_folder = mock.MagicMock()
        work_folder.exists.return_value = True
        config = PoodleConfigStub(work_folder=work_folder, echo_enabled=True, min_timeout=10, timeout_multiplier=10)

        reporter1 = mock.MagicMock()
        reporter2 = mock.MagicMock()
        generate_reporters.return_value = iter([reporter1, reporter2])

        mutant1 = mock.MagicMock()
        mutant2 = mock.MagicMock()
        create_mutants_for_all_mutators.return_value = [mutant1, mutant2]

        clean_run_each_source_folder.return_value = {"folder": MutantTrial(mutant=None, result=None, duration=1.0)}  # type: ignore [arg-type]

        core.main_process(config)

        poodle_work_class.assert_called_with(config)
        work = poodle_work_class.return_value

        print_header.assert_called_with(work)

        pprint_str.assert_called_with(config)
        logger_mock.info.assert_has_calls(
            [
                mock.call("\n%s", pprint_str.return_value),
                mock.call("delete %s", work_folder),
            ]
        )
        assert logger_mock.info.call_count == 3

        work_folder.exists.assert_called()
        logger_mock.info.assert_any_call("delete %s", work_folder)

        shutil.rmtree.assert_called_with(work_folder)
        assert shutil.rmtree.call_count == 2

        create_temp_zips.assert_called_with(work)

        initialize_mutators.assert_called_with(work)
        assert work.mutators == initialize_mutators.return_value
        get_runner.assert_called_with(config)
        assert work.runner == get_runner.return_value
        generate_reporters.assert_called_with(config)
        assert work.reporters == [reporter1, reporter2]

        create_mutants_for_all_mutators.assert_called_with(work)
        work.echo.assert_called_with("Identified 2 mutants")

        clean_run_each_source_folder.assert_called_with(work)
        run_mutant_trails.assert_called_with(work, [mutant1, mutant2], 10.0)
        results = run_mutant_trails.return_value

        reporter1.assert_called_with(config=config, echo=work.echo, testing_results=results)
        reporter2.assert_called_with(config=config, echo=work.echo, testing_results=results)

        logger_mock.info.assert_any_call("delete %s", work_folder)

    @mock.patch("poodle.core.PoodleWork")
    @mock.patch("poodle.core.pprint_str")
    @mock.patch("poodle.core.shutil")
    @mock.patch("poodle.core.create_temp_zips")
    @mock.patch("poodle.core.initialize_mutators")
    @mock.patch("poodle.core.get_runner")
    @mock.patch("poodle.core.generate_reporters")
    @mock.patch("poodle.core.create_mutants_for_all_mutators")
    @mock.patch("poodle.core.clean_run_each_source_folder")
    @mock.patch("poodle.core.run_mutant_trails")
    @mock.patch("poodle.core.click")
    def test_main_not_exists(
        self,
        core_click: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
        clean_run_each_source_folder: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
        generate_reporters: mock.MagicMock,
        get_runner: mock.MagicMock,
        initialize_mutators: mock.MagicMock,
        create_temp_zips: mock.MagicMock,
        shutil: mock.MagicMock,
        pprint_str: mock.MagicMock,
        poodle_work_class: mock.MagicMock,
        logger_mock: mock.MagicMock,
    ):
        work_folder = mock.MagicMock()
        work_folder.exists.return_value = False
        config = PoodleConfigStub(work_folder=work_folder, echo_enabled=True, min_timeout=10, timeout_multiplier=10)

        reporter1 = mock.MagicMock()
        reporter2 = mock.MagicMock()
        generate_reporters.return_value = iter([reporter1, reporter2])

        mutant1 = mock.MagicMock()
        mutant2 = mock.MagicMock()
        create_mutants_for_all_mutators.return_value = [mutant1, mutant2]

        clean_run_each_source_folder.return_value = {"folder": MutantTrial(mutant=None, result=None, duration=1.0)}  # type: ignore [arg-type]

        core.main_process(config)

        logger_mock.info.assert_has_calls(
            [
                mock.call("\n%s", pprint_str.return_value),
                mock.call("delete %s", work_folder),
            ]
        )
        assert logger_mock.info.call_count == 2

        shutil.rmtree.assert_called_with(work_folder)
        assert shutil.rmtree.call_count == 1

    @mock.patch("poodle.core.PoodleWork")
    @mock.patch("poodle.core.pprint_str")
    @mock.patch("poodle.core.shutil")
    @mock.patch("poodle.core.create_temp_zips")
    @mock.patch("poodle.core.initialize_mutators")
    @mock.patch("poodle.core.get_runner")
    @mock.patch("poodle.core.generate_reporters")
    @mock.patch("poodle.core.create_mutants_for_all_mutators")
    @mock.patch("poodle.core.clean_run_each_source_folder")
    @mock.patch("poodle.core.run_mutant_trails")
    @mock.patch("poodle.core.click")
    def test_input_error(
        self,
        core_click: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
        clean_run_each_source_folder: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
        generate_reporters: mock.MagicMock,
        get_runner: mock.MagicMock,
        initialize_mutators: mock.MagicMock,
        create_temp_zips: mock.MagicMock,
        shutil: mock.MagicMock,
        pprint_str: mock.MagicMock,
        poodle_work_class: mock.MagicMock,
        logger_mock: mock.MagicMock,
    ):
        poodle_work_class.side_effect = [PoodleInputError("Input Error", "Bad Input")]

        core.main_process(PoodleConfigStub())

        core_click.echo.assert_any_call("Input Error")
        core_click.echo.assert_any_call("Bad Input")

    @mock.patch("poodle.core.PoodleWork")
    @mock.patch("poodle.core.pprint_str")
    @mock.patch("poodle.core.shutil")
    @mock.patch("poodle.core.create_temp_zips")
    @mock.patch("poodle.core.initialize_mutators")
    @mock.patch("poodle.core.get_runner")
    @mock.patch("poodle.core.generate_reporters")
    @mock.patch("poodle.core.create_mutants_for_all_mutators")
    @mock.patch("poodle.core.clean_run_each_source_folder")
    @mock.patch("poodle.core.run_mutant_trails")
    @mock.patch("poodle.core.click")
    def test_trial_error(
        self,
        core_click: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
        clean_run_each_source_folder: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
        generate_reporters: mock.MagicMock,
        get_runner: mock.MagicMock,
        initialize_mutators: mock.MagicMock,
        create_temp_zips: mock.MagicMock,
        shutil: mock.MagicMock,
        pprint_str: mock.MagicMock,
        poodle_work_class: mock.MagicMock,
        logger_mock: mock.MagicMock,
    ):
        poodle_work_class.side_effect = [PoodleTrialRunError("Trial Error", "Execution Failed")]

        core.main_process(PoodleConfigStub())

        core_click.echo.assert_any_call("Trial Error")
        core_click.echo.assert_any_call("Execution Failed")


poodle_header_str = r"""
|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|
    ____                  ____         ''',
   / __ \____  ____  ____/ / /__    o_)O \)____)"
  / /_/ / __ \/ __ \/ __  / / _ \    \_        )
 / ____/ /_/ / /_/ / /_/ / /  __/      '',,,,,,
/_/    \____/\____/\__,_/_/\___/         ||  ||
Mutation Tester Version 1.2.3           "--'"--'
|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|

"""


class TestPrintHeader:
    def test_print_header(self):
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=["src"],
                config_file="config_file.toml",
                max_workers=10,
                runner="pytest",
                reporters=["summary", "json"],
            )
        )
        work.echo = mock.MagicMock()

        with mock.patch("poodle.core.__version__", "1.2.3"):
            core.print_header(work)

        work.echo.assert_has_calls(
            [
                mock.call(poodle_header_str, fg="blue"),
                mock.call("Running with the following configuration:"),
                mock.call(" - Source Folders: ['src']"),
                mock.call(" - Config File:    config_file.toml"),
                mock.call(" - Max Workers:    10"),
                mock.call(" - Runner:         pytest"),
                mock.call(" - Reporters:      ['summary', 'json']"),
                mock.call(),
            ]
        )
