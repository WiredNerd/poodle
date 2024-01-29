"""Resolve configuration options and build PoodleConfig object."""

from __future__ import annotations

import logging
import os
from contextlib import suppress
from functools import cached_property
from pathlib import Path

from ordered_set import OrderedSet
from wcmatch import glob

from .config_base import PoodleConfigBase
from .exceptions import PoodleInputError


class PoodleConfigData(PoodleConfigBase):
    """Poodle Configuration Data Properties."""

    default_log_format = "%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"

    @cached_property
    def log_format(self) -> str:
        """Log Format."""
        return self.get_str_from_config("log_format") or self.default_log_format

    @cached_property
    def verbosity_level(self) -> int:
        """Calculated verbosity level from command line."""
        cmd_quiet = self.cmd_kwargs.get("quiet", 0)
        cmd_verbose = self.cmd_kwargs.get("verbose", 0)
        return cmd_verbose - cmd_quiet

    def _get_cmd_line_log_level(self) -> int | None:
        """Map verbosity input to logging level."""
        if self.verbosity_level >= 2:
            return logging.CRITICAL
        elif self.verbosity_level == 1:
            return logging.ERROR
        elif self.verbosity_level == 0:
            return logging.WARN
        elif self.verbosity_level == -1:
            return logging.INFO
        else:
            return logging.DEBUG

    @cached_property
    def log_level(self) -> int | str:
        """Log Level."""
        return self.get_any_from_config("log_level") or self._get_cmd_line_log_level()

    @cached_property
    def project_name(self) -> str:
        """Project Name."""
        project_name = self.get_str_from_config("project_name")

        if project_name:
            return project_name

        with suppress(KeyError):
            return self._pyproject_toml["project"]["name"]

        # TODO: tox.ini and setup.cfg
        # https://tox.wiki/en/3.24.5/config.html

        return ""

    @cached_property
    def project_version(self) -> str:
        """Project Version."""
        project_version = self.get_str_from_config("project_version")

        if project_version:
            return project_version

        with suppress(KeyError):
            return self._pyproject_toml["project"]["version"]

        # TODO: tox.ini and setup.cfg
        # https://tox.wiki/en/3.24.5/config.html

        return ""

    default_source_folders = [Path("src"), Path("lib")]

    @cached_property
    def source_folders(self) -> list[Path]:
        """List of source folders that contain files to mutate.

        Verifies that all returned values are existing directories.
        """
        default = [source for source in self.default_source_folders if source.is_dir()]
        source_folders = self.get_path_list_from_config("source_folders", "sources") or default

        if not source_folders:
            raise PoodleInputError("No source folder found to mutate.")

        for source in source_folders:
            if not source.is_dir():
                msg = f"Source '{source}' must be a folder."
                raise PoodleInputError(msg)

        return source_folders

    default_file_flags = glob.GLOBSTAR | glob.NODIR

    @cached_property
    def file_flags(self) -> int:
        """This option is to set the flags used when searching source folders for files to mutate."""
        return self.get_int_from_config("file_flags") or self.default_file_flags

    @cached_property
    def only_files(self) -> list[str]:
        """Only mutate these files."""
        return self.get_str_list_from_config("only_files", "only") or []

    default_file_filters = ["test_*.py", "*_test.py", "poodle_config.py", "setup.py"]

    @cached_property
    def file_filters(self) -> list[str]:
        """List of file filters to exclude from mutation."""
        file_filters = self.get_str_list_from_config("file_filters") or self.default_file_filters
        file_filters += self.get_str_list_from_config("exclude") or []
        file_filters += self.cmd_kwargs.get("exclude", [])
        return file_filters

    default_file_copy_flags = glob.GLOBSTAR | glob.NODIR

    @cached_property
    def file_copy_flags(self) -> int:
        """This option is to set the flags used when searching source folders for files to copy."""
        return self.get_int_from_config("file_copy_flags") or self.default_file_copy_flags

    default_file_copy_filters = ["__pycache__/**"]

    @cached_property
    def file_copy_filters(self) -> list[str]:
        """List of file filters to exclude from copy."""
        return self.get_str_list_from_config("file_copy_filters") or self.default_file_copy_filters

    default_work_folder = Path(".poodle-temp")

    @cached_property
    def work_folder(self) -> Path:
        """Folder to store temporary files."""
        return self.get_path_from_config("work_folder") or self.default_work_folder

    @staticmethod
    def default_max_workers() -> int:
        """Calculate Default for max_workers as one less than available processors."""
        if hasattr(os, "sched_getaffinity"):
            return len(os.sched_getaffinity(0)) - 1
        cpu_count = os.cpu_count() or 1  # nomut: Number
        if cpu_count > 1:
            return cpu_count - 1
        return cpu_count

    @cached_property
    def max_workers(self) -> int:
        """Maximum number of workers to use."""
        return self.get_int_from_config("max_workers", "workers") or self.default_max_workers()

    @cached_property
    def skip_delete_folder(self) -> bool:
        """Enable/Disable echo statements."""
        return self.get_bool_from_config("skip_delete_folder") or False

    def _get_cmd_line_echo_enabled(self) -> bool | None:
        """Map verbosity input to enable/disable echo statements."""
        if self.verbosity_level < 0:
            return False
        if self.verbosity_level > 0:
            return True
        return None

    @cached_property
    def echo_enabled(self) -> bool:
        """Enable/Disable echo statements."""
        cmd_echo_enabled = self._get_cmd_line_echo_enabled()

        if cmd_echo_enabled is not None:
            return cmd_echo_enabled

        cfg_echo_enabled = self.get_bool_from_config("echo_enabled")

        if cfg_echo_enabled is not None:
            return cfg_echo_enabled

        return True

    @cached_property
    def echo_no_color(self) -> bool:
        """Enable/Disable echo statements."""
        return self.get_bool_from_config("echo_no_color") or False

    default_mutator_filter_patterns = [
        r'.*__name__\s*==\s*(\'|")__main__(\'|").*',
    ]

    @cached_property
    def mutator_filter_patterns(self) -> list[str]:
        """List of filter patterns to exclude from mutation."""
        filter_patterns = self.default_mutator_filter_patterns
        filter_patterns += self.get_str_list_from_config("mutator_filter_patterns") or []
        return filter_patterns

    @cached_property
    def skip_mutators(self) -> list[str]:
        """List of disabled mutators."""
        names = self.get_str_list_from_config("skip_mutators") or []
        return [name.lower() for name in names]

    @cached_property
    def only_mutators(self) -> list[str]:
        """List of enabled mutators.  Overrides skip_mutators."""
        names = self.get_str_list_from_config("only_mutators") or []
        return [name.lower() for name in names]

    default_min_timeout = 10

    @cached_property
    def min_timeout(self) -> int:
        """Minimum timeout value to use in runner."""
        return self.get_int_from_config("min_timeout") or self.default_min_timeout

    default_timeout_multiplier = 10

    @cached_property
    def timeout_multiplier(self) -> int:
        """Timeout multiplier to use in runner."""
        return self.get_int_from_config("timeout_multiplier") or self.default_timeout_multiplier

    default_runner = "command_line"

    @cached_property
    def runner(self) -> str:
        """Name of runner to use."""
        return self.get_str_from_config("runner") or self.default_runner

    default_reporters = ["sysout"]

    @cached_property
    def reporters(self) -> OrderedSet[str]:
        """Retrieve list of reporters to use."""
        return OrderedSet(self.get_str_list_from_config("reporters", "report") or self.default_reporters)
