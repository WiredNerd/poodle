from unittest import mock

import pytest

from poodle import PoodleNoMutantsFoundError, PoodleTestingFailedError, core
from poodle.data_types import MutantTrial, PoodleWork
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def logger_mock():
    with mock.patch("poodle.core.logger") as logger_mock:
        yield logger_mock


def test_logger():
    assert core.logger.name == "poodle.core"


class TestMainProcess:
    @pytest.fixture()
    def poodle_work_class(self):
        with mock.patch("poodle.core.PoodleWork") as poodle_work_class:
            yield poodle_work_class

    @pytest.fixture()
    def print_header(self):
        with mock.patch("poodle.core.print_header") as print_header:
            yield print_header

    @pytest.fixture()
    def pprint_str(self):
        with mock.patch("poodle.core.pprint_str") as pprint_str:
            yield pprint_str

    @pytest.fixture()
    def delete_folder(self):
        with mock.patch("poodle.core.delete_folder") as delete_folder:
            yield delete_folder

    @pytest.fixture()
    def create_temp_zips(self):
        with mock.patch("poodle.core.create_temp_zips") as create_temp_zips:
            yield create_temp_zips

    @pytest.fixture()
    def initialize_mutators(self):
        with mock.patch("poodle.core.initialize_mutators") as initialize_mutators:
            yield initialize_mutators

    @pytest.fixture()
    def get_runner(self):
        with mock.patch("poodle.core.get_runner") as get_runner:
            yield get_runner

    @pytest.fixture()
    def generate_reporters(self):
        with mock.patch("poodle.core.generate_reporters") as generate_reporters:
            yield generate_reporters

    @pytest.fixture()
    def create_mutants_for_all_mutators(self):
        with mock.patch("poodle.core.create_mutants_for_all_mutators") as create_mutants_for_all_mutators:
            yield create_mutants_for_all_mutators

    @pytest.fixture()
    def clean_run_each_source_folder(self):
        with mock.patch("poodle.core.clean_run_each_source_folder") as clean_run_each_source_folder:
            yield clean_run_each_source_folder

    @pytest.fixture()
    def calc_timeout(self):
        with mock.patch("poodle.core.calc_timeout") as calc_timeout:
            yield calc_timeout

    @pytest.fixture()
    def run_mutant_trails(self):
        with mock.patch("poodle.core.run_mutant_trails") as run_mutant_trails:
            yield run_mutant_trails

    @pytest.fixture()
    def create_unified_diff(self):
        with mock.patch("poodle.core.create_unified_diff") as create_unified_diff:
            yield create_unified_diff

    @pytest.fixture()
    def _setup_main_process(
        self,
        poodle_work_class: mock.MagicMock,
        print_header: mock.MagicMock,
        pprint_str: mock.MagicMock,
        delete_folder: mock.MagicMock,
        create_temp_zips: mock.MagicMock,
        initialize_mutators: mock.MagicMock,
        get_runner: mock.MagicMock,
        generate_reporters: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
        clean_run_each_source_folder: mock.MagicMock,
        calc_timeout: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
        create_unified_diff: mock.MagicMock,
        logger_mock: mock.MagicMock,
    ):
        poodle_work_class.reset_mock()
        print_header.reset_mock()
        pprint_str.reset_mock()
        delete_folder.reset_mock()
        create_temp_zips.reset_mock()
        initialize_mutators.reset_mock()
        get_runner.reset_mock()
        generate_reporters.reset_mock()
        create_mutants_for_all_mutators.reset_mock()
        clean_run_each_source_folder.reset_mock()
        calc_timeout.reset_mock()
        run_mutant_trails.reset_mock()
        create_unified_diff.reset_mock()
        logger_mock.reset_mock()

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_setup(
        self,
        poodle_work_class: mock.MagicMock,
        print_header: mock.MagicMock,
        pprint_str: mock.MagicMock,
        logger_mock: mock.MagicMock,
        delete_folder: mock.MagicMock,
        create_temp_zips: mock.MagicMock,
    ):
        config = PoodleConfigStub()

        core.main_process(config)

        poodle_work_class.assert_called_once_with(config)
        work = poodle_work_class.return_value

        print_header.assert_called_once_with(work)

        pprint_str.assert_called_once_with(config)
        logger_mock.info.assert_called_once_with("\n%s", pprint_str.return_value)

        delete_folder.assert_called_with(config.work_folder)
        assert delete_folder.call_count == 2

        create_temp_zips.assert_called_once_with(work)

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_init(
        self,
        poodle_work_class: mock.MagicMock,
        initialize_mutators: mock.MagicMock,
        get_runner: mock.MagicMock,
        generate_reporters: mock.MagicMock,
    ):
        config = PoodleConfigStub()

        reporter1 = mock.MagicMock()
        reporter2 = mock.MagicMock()
        generate_reporters.return_value = iter([reporter1, reporter2])

        core.main_process(config)

        work = poodle_work_class.return_value

        initialize_mutators.assert_called_once_with(work)
        get_runner.assert_called_once_with(config)
        generate_reporters.assert_called_once_with(config)

        assert work.mutators == initialize_mutators.return_value
        assert work.runner == get_runner.return_value
        assert work.reporters == [reporter1, reporter2]

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_mutants(
        self,
        poodle_work_class: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
    ):
        config = PoodleConfigStub()

        core.main_process(config)

        work = poodle_work_class.return_value

        create_mutants_for_all_mutators.assert_called_once_with(work)
        mutants = create_mutants_for_all_mutators.return_value
        work.echo.assert_called_once_with(f"Identified {len(mutants)} mutants")

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_mutants_empty(
        self,
        create_mutants_for_all_mutators: mock.MagicMock,
    ):
        config = PoodleConfigStub()

        create_mutants_for_all_mutators.return_value = []

        with pytest.raises(PoodleNoMutantsFoundError, match=r"^No mutants were found to test!$"):
            core.main_process(config)

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_run(
        self,
        poodle_work_class: mock.MagicMock,
        create_mutants_for_all_mutators: mock.MagicMock,
        clean_run_each_source_folder: mock.MagicMock,
        calc_timeout: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
    ):
        config = PoodleConfigStub()

        core.main_process(config)

        work = poodle_work_class.return_value
        mutants = create_mutants_for_all_mutators.return_value

        clean_run_each_source_folder.assert_called_once_with(work)
        clean_run_results = clean_run_each_source_folder.return_value
        calc_timeout.assert_called_once_with(config, clean_run_results)
        timeout = calc_timeout.return_value
        run_mutant_trails.assert_called_once_with(work, mutants, timeout)

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_report(
        self,
        poodle_work_class: mock.MagicMock,
        run_mutant_trails: mock.MagicMock,
        generate_reporters: mock.MagicMock,
        create_unified_diff: mock.MagicMock,
    ):
        config = PoodleConfigStub()

        results = run_mutant_trails.return_value
        trial1 = MutantTrial(mutant=mock.MagicMock(name="mutant1"), result=mock.MagicMock(name="result1"), duration=1.0)
        trial2 = MutantTrial(mutant=mock.MagicMock(name="mutant2"), result=mock.MagicMock(name="result2"), duration=1.0)
        results.mutant_trials = [trial1, trial2]

        reporter1 = mock.MagicMock(name="reporter1")
        reporter2 = mock.MagicMock(name="reporter2")
        generate_reporters.return_value = iter([reporter1, reporter2])

        core.main_process(config)

        work = poodle_work_class.return_value

        create_unified_diff.assert_has_calls([mock.call(trial1.mutant), mock.call(trial2.mutant)])
        assert trial1.mutant.unified_diff == create_unified_diff.return_value
        assert trial2.mutant.unified_diff == create_unified_diff.return_value

        reporter1.assert_called_once_with(config=config, echo=work.echo, testing_results=results)
        reporter2.assert_called_once_with(config=config, echo=work.echo, testing_results=results)

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_fail_under_pass(
        self,
        run_mutant_trails: mock.MagicMock,
    ):
        config = PoodleConfigStub(fail_under=80.0)

        results = run_mutant_trails.return_value
        results.summary.success_rate = 0.8
        results.summary.coverage_display = "80.00%"

        core.main_process(config)
        # no error reported

    @pytest.mark.usefixtures("_setup_main_process")
    def test_main_process_fail_under_fail(
        self,
        run_mutant_trails: mock.MagicMock,
    ):
        config = PoodleConfigStub(fail_under=80.0)

        results = run_mutant_trails.return_value
        results.summary.success_rate = 0.7999
        results.summary.coverage_display = "79.9%"

        with pytest.raises(PoodleTestingFailedError, match=r"^Mutation score 79.9% is below goal of 80%$"):
            core.main_process(config)


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
                fail_under=None,
            )
        )
        work.echo = mock.MagicMock()

        with mock.patch("poodle.core.__version__", "1.2.3"):
            core.print_header(work)

        work.echo.assert_has_calls(
            [
                mock.call(poodle_header_str, fg="cyan"),
                mock.call("Running with the following configuration:"),
                mock.call(" - Source Folders: ['src']"),
                mock.call(" - Config File:    config_file.toml"),
                mock.call(" - Max Workers:    10"),
                mock.call(" - Runner:         pytest"),
                mock.call(" - Reporters:      ['summary', 'json']"),
                mock.call(),
            ]
        )

    def test_print_header_goal(self):
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=["src"],
                config_file="config_file.toml",
                max_workers=10,
                runner="pytest",
                reporters=["summary", "json"],
                fail_under=53.4,
            )
        )
        work.echo = mock.MagicMock()

        with mock.patch("poodle.core.__version__", "1.2.3"):
            core.print_header(work)

        work.echo.assert_has_calls(
            [
                mock.call(poodle_header_str, fg="cyan"),
                mock.call("Running with the following configuration:"),
                mock.call(" - Source Folders: ['src']"),
                mock.call(" - Config File:    config_file.toml"),
                mock.call(" - Max Workers:    10"),
                mock.call(" - Runner:         pytest"),
                mock.call(" - Reporters:      ['summary', 'json']"),
                mock.call(" - Coverage Goal:  53.40%"),
                mock.call(),
            ]
        )


class TestDeleteFolder:
    @pytest.fixture()
    def shutil(self):
        with mock.patch("poodle.core.shutil") as shutil:
            yield shutil

    def test_delete_folder_exists(self, shutil, logger_mock):
        folder = mock.MagicMock()
        folder.exists.return_value = True

        core.delete_folder(folder)

        logger_mock.info.assert_called_once_with("delete %s", folder)
        shutil.rmtree.assert_called_once_with(folder)

    def test_delete_folder_not_exists(self, shutil, logger_mock):
        folder = mock.MagicMock()
        folder.exists.return_value = False

        core.delete_folder(folder)

        logger_mock.info.assert_not_called()
        shutil.rmtree.assert_not_called()
