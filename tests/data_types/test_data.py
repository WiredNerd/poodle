from pathlib import Path

from poodle.data_types.data import FileMutation, Mutant, MutantTrial, MutantTrialResult, PoodleConfig


class TestPoodleConfig:
    @classmethod
    def create_poodle_config(cls):
        return PoodleConfig(
            config_file=Path("filename.toml"),
            source_folders=[Path("src")],
            file_filters=["test_"],
            file_copy_filters=["skip"],
            work_folder=Path(".poodle"),
            log_format="$(message)s",
            log_level=0,
            echo_enabled=True,
            mutator_opts={"bin_op_level": 2},
            skip_mutators=["null"],
            add_mutators=["custom"],
            runner="command_line",
            runner_opts={"command_line": "pytest tests"},
            reporters=["summary"],
            reporter_opts={"summary": "value"},
        )

    def test_poodle_config(self):
        config = self.create_poodle_config()

        assert config.config_file == Path("filename.toml")
        assert config.source_folders == [Path("src")]
        assert config.file_filters == ["test_"]
        assert config.file_copy_filters == ["skip"]
        assert config.work_folder == Path(".poodle")
        assert config.log_format == "$(message)s"
        assert config.log_level == 0
        assert config.echo_enabled == True
        assert config.mutator_opts == {"bin_op_level": 2}
        assert config.skip_mutators == ["null"]
        assert config.add_mutators == ["custom"]
        assert config.runner == "command_line"
        assert config.runner_opts == {"command_line": "pytest tests"}
        assert config.reporters == ["summary"]
        assert config.reporter_opts == {"summary": "value"}


class TestFileMutation:
    @classmethod
    def create_file_mutation(cls):
        return FileMutation(
            lineno=1,
            col_offset=2,
            end_lineno=3,
            end_col_offset=4,
            text="mutant",
        )

    def test_file_mutant(self):
        file_mutant = self.create_file_mutation()

        assert file_mutant.lineno == 1
        assert file_mutant.col_offset == 2
        assert file_mutant.end_lineno == 3
        assert file_mutant.end_col_offset == 4
        assert file_mutant.text == "mutant"


class TestMutant:
    def test_init(self):
        poodle_mutant = Mutant(
            source_folder=Path("src"),
            source_file=Path("test.py"),
            **vars(TestFileMutation.create_file_mutation()),
        )

        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file == Path("test.py")
        assert poodle_mutant.lineno == 1
        assert poodle_mutant.col_offset == 2
        assert poodle_mutant.end_lineno == 3
        assert poodle_mutant.end_col_offset == 4
        assert poodle_mutant.text == "mutant"

    def test_poodle_mutant_min(self):
        poodle_mutant = Mutant(
            source_folder=Path("src"),
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        )

        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file is None
        assert poodle_mutant.lineno == 0
        assert poodle_mutant.col_offset == 0
        assert poodle_mutant.end_lineno == 0
        assert poodle_mutant.end_col_offset == 0
        assert poodle_mutant.text == ""


class TestMutantTrialResult:
    def test_mutant_trial_result(self):
        result = MutantTrialResult(passed=True, reason_code="test", reason_desc="it worked")

        assert result.passed is True
        assert result.reason_code == "test"
        assert result.reason_desc == "it worked"
        assert result.RC_FOUND == "mutant_found"
        assert result.RC_NOT_FOUND == "mutant_not_found"
        assert result.RC_TIMEOUT == "timeout"
        assert result.RC_INCOMPLETE == "incomplete"
        assert result.RC_OTHER == "other"

    def test_mutant_trial_result_min(self):
        result = MutantTrialResult(
            passed=True,
            reason_code="test",
        )

        assert result.passed is True
        assert result.reason_code == "test"
        assert result.reason_desc is None
        assert result.RC_FOUND == "mutant_found"
        assert result.RC_NOT_FOUND == "mutant_not_found"
        assert result.RC_TIMEOUT == "timeout"
        assert result.RC_INCOMPLETE == "incomplete"
        assert result.RC_OTHER == "other"


class TestMutantTrial:
    def test_mutant_trial(self):
        mutant = Mutant(source_folder=Path("."), source_file=None, **vars(TestFileMutation.create_file_mutation()))
        result = MutantTrialResult(passed=True, reason_code="test")
        trial = MutantTrial(mutant=mutant, result=result)
        assert trial.mutant == mutant
        assert trial.result == result
