"""Poodle Mutation Test Tool."""

from __future__ import annotations

__version__ = "2.0.0"

from poodle.common.base import PoodleOptionCollector
from poodle.common.config import PoodleConfigData
from poodle.common.data import (
    FileMutation,
    Mutant,
    MutantTrial,
    MutantTrialResult,
    PoodleConfig,
    PoodleSerialize,
    TestingResults,
    TestingSummary,
)
from poodle.common.exceptions import (
    PoodleInputError,
    PoodleNoMutantsFoundError,
    PoodleTestingFailedError,
    PoodleTrialRunError,
)
from poodle.common.interfaces import Mutator
from poodle.common.mutator_base import MutatorBase
from poodle.common.work import PoodleWork
