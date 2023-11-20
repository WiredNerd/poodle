from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any, Callable

from .data_types import PoodleConfig
from .reporters import report_not_found, report_summary
from .util import dynamic_import

logger = logging.getLogger(__name__)

builtin_reporters = {
    "summary": report_summary,
    "not_found": report_not_found,
}


def generate_reporters(config: PoodleConfig) -> Generator[Callable, Any, None]:
    """Build list of reporter functions."""
    logger.debug("Reporters: %s", config.reporters)

    if config.reporters:
        for reporter_name in config.reporters:
            if reporter_name in builtin_reporters:
                yield builtin_reporters[reporter_name]
            else:
                yield dynamic_import(reporter_name)
