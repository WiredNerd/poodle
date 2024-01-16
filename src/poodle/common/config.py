"""Resolve configuration options and build PoodleConfig object."""

from __future__ import annotations

import logging
import os
from contextlib import suppress
from functools import cached_property
from pathlib import Path

from ordered_set import OrderedSet
from wcmatch import glob

from .base import PoodleConfigBase
from .exceptions import PoodleInputError


class PoodleConfigData(PoodleConfigBase):
    """Poodle Configuration Data Properties."""

    default_log_format = "%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"

    default_source_folders = [Path("src"), Path("lib")]

    default_file_flags = glob.GLOBSTAR | glob.NODIR
    default_file_filters = ["test_*.py", "*_test.py", "poodle_config.py", "setup.py"]

    default_file_copy_flags = glob.GLOBSTAR | glob.NODIR
    default_file_copy_filters = ["__pycache__/**"]

    default_work_folder = Path(".poodle-temp")

    default_mutator_filter_patterns = [
        r'.*__name__\s*==\s*(\'|")__main__(\'|").*',
    ]

    # default_min_timeout = 10
    # default_timeout_multiplier = 10
    # default_runner = "command_line"

    default_reporters = ["sysout"]

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

    @cached_property
    def file_flags(self) -> int:
        """This option is to set the flags used when searching source folders for files to mutate."""
        return self.get_int_from_config("file_flags") or self.default_file_flags

    @cached_property
    def only_files(self) -> list[str]:
        """Only mutate these files."""
        return self.get_str_list_from_config("only_files", "only") or []

    @cached_property
    def file_filters(self) -> list[str]:
        """List of file filters to exclude from mutation."""
        file_filters = self.get_str_list_from_config("file_filters") or self.default_file_filters
        file_filters += self.get_str_list_from_config("exclude") or []
        file_filters += self.cmd_kwargs.get("exclude", [])
        return file_filters

    @cached_property
    def file_copy_flags(self) -> int:
        """This option is to set the flags used when searching source folders for files to copy."""
        return self.get_int_from_config("file_copy_flags") or self.default_file_copy_flags

    @cached_property
    def file_copy_filters(self) -> list[str]:
        """List of file filters to exclude from copy."""
        return self.get_str_list_from_config("file_copy_filters") or self.default_file_copy_filters

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

    def _get_cmd_line_echo_enabled(self) -> bool | None:
        """Map verbosity input to enable/disable echo statements."""
        self.verbosity_level
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

    @cached_property
    def reporters(self) -> OrderedSet[str]:
        """Retrieve list of reporters to use."""
        return OrderedSet(self.get_str_list_from_config("reporters", "report") or self.default_reporters)

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


#     cmd_fail_under: float | None,

#         mutator_opts=get_dict_from_config("mutator_opts", config_file_data),
#         add_mutators=get_any_list_from_config("add_mutators", config_file_data),
#         min_timeout=get_int_from_config("min_timeout", config_file_data) or default_min_timeout,
#         timeout_multiplier=get_int_from_config("timeout_multiplier", config_file_data) or default_timeout_multiplier,
#         runner=get_str_from_config("runner", config_file_data, default=default_runner),
#         runner_opts=get_dict_from_config("runner_opts", config_file_data),
#         fail_under=get_float_from_config("fail_under", config_file_data, command_line=cmd_fail_under),
#         skip_delete_folder=get_bool_from_config("skip_delete_folder", config_file_data, default=False),
