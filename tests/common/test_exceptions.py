import pytest

from poodle.common.exceptions import (
    PoodleInputError,
    PoodleNoMutantsFoundError,
    PoodleTestingFailedError,
    PoodleTrialRunError,
)


class TestPoodleExceptions:
    def test_poodle_testing_failed_error(self):
        with pytest.raises(PoodleTestingFailedError, match="^Poodle testing failed.$"):
            raise PoodleTestingFailedError("Poodle testing failed.")

    def test_poodle_no_mutants_found_error(self):
        with pytest.raises(PoodleNoMutantsFoundError, match="^Poodle could not find any mutants to test.$"):
            raise PoodleNoMutantsFoundError("Poodle could not find any mutants to test.")

    def test_poodle_input_error(self):
        with pytest.raises(PoodleInputError, match="^Poodle input error.$"):
            raise PoodleInputError("Poodle input error.")

    def test_poodle_unexpected_error(self):
        with pytest.raises(PoodleTrialRunError, match="^Poodle unexpected error.$"):
            raise PoodleTrialRunError("Poodle unexpected error.")
