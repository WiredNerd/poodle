"""Report Testing Results."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from .reporters import report_html, report_json, report_not_found, report_summary
from .util import dynamic_import

if TYPE_CHECKING:
    from collections.abc import Generator

    from .data_types import PoodleConfig

logger = logging.getLogger(__name__)

builtin_reporters: dict[str, Callable] = {
    "summary": report_summary,
    "not_found": report_not_found,
    "json": report_json,
    "html": report_html,
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
