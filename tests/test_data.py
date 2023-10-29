from pathlib import Path

from poodle.data import FileMutant, PoodleConfig, PoodleMutant, PoodleTestResult, PoodleWork


class TestPoodleConfig:
    @classmethod
    def create_poodle_config(cls):
        return PoodleConfig(
            config_file="filename.toml",
            source_folders=[Path("src")],
            file_filters=["test_"],
            work_folder=Path(".poodle"),
            runner_cmd="pytest",
            mutator_opts={"bin_op_level": 2},
        )

    def test_poodle_config(self):
        config = self.create_poodle_config()

        assert config.config_file == "filename.toml"
        assert config.source_folders == [Path("src")]
        assert config.file_filters == ["test_"]
        assert config.work_folder == Path(".poodle")
        assert config.runner_cmd == "pytest"
        assert config.mutator_opts == {"bin_op_level": 2}


class TestPoodleWork:
    def test_poodle_work(self):
        work = PoodleWork(config=TestPoodleConfig.create_poodle_config())

        assert work.config.config_file == "filename.toml"
        assert work.folder_zips == {}
        assert work.next_num() == "1"
        assert work.next_num() == "2"


class TestFileMutant:
    @classmethod
    def create_file_mutant(cls):
        return FileMutant(
            lineno=1,
            col_offset=2,
            end_lineno=3,
            end_col_offset=4,
            text="mutant",
        )

    def test_file_mutant(self):
        file_mutant = self.create_file_mutant()

        assert file_mutant.lineno == 1
        assert file_mutant.col_offset == 2
        assert file_mutant.end_lineno == 3
        assert file_mutant.end_col_offset == 4
        assert file_mutant.text == "mutant"


class TestPoodleMutant:
    def test_poodle_mutant(self):
        poodle_mutant = PoodleMutant.from_file_mutant(
            source_folder=Path("src"),
            source_file=Path("test.py"),
            file_mutant=TestFileMutant.create_file_mutant(),
        )

        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file == Path("test.py")
        assert poodle_mutant.lineno == 1
        assert poodle_mutant.col_offset == 2
        assert poodle_mutant.end_lineno == 3
        assert poodle_mutant.end_col_offset == 4
        assert poodle_mutant.text == "mutant"

    def test_poodle_mutant_min(self):
        poodle_mutant = PoodleMutant(
            source_folder=Path("src"),
        )

        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file is None
        assert poodle_mutant.lineno is None
        assert poodle_mutant.col_offset is None
        assert poodle_mutant.end_lineno is None
        assert poodle_mutant.end_col_offset is None
        assert poodle_mutant.text is None


class TestPoodleTestResult:
    def test_poodle_test_result(self):
        result = PoodleTestResult(
            test_passed=True,
            reason_code="test",
        )

        assert result.test_passed is True
        assert result.reason_code == "test"
        assert result.reason_desc is None
        assert result.RC_FOUND == "mutant_found"
        assert result.RC_NOT_FOUND == "mutant_not_found"
        assert result.RC_TIMEOUT == "timeout"
        assert result.RC_INCOMPLETE == "incomplete"
        assert result.RC_OTHER == "other"
