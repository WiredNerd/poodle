from contextlib import suppress
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from poodle import PoodleInvalidInput
from poodle.data import PoodleConfig

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

poodle_config: Any = None
with suppress(ImportError):
    import poodle_config  # type: ignore

default_source_folders = [Path("src"), Path("lib")]
default_file_filters = [r"^test_", r"_test$"]
default_work_folder = Path(".poodle-temp")
default_mutator_opts = {}
default_runner_opts = {"command_line": "pytest -x --assert=plain --no-header --no-summary -o pythonpath="}


def build_config(command_line_sources: Tuple[Path], config_file: Optional[Path]):
    config_file_path = get_config_file_path(config_file)
    config_file_data = get_config_file_data(config_file_path)

    return PoodleConfig(
        config_file=config_file_path,
        source_folders=get_source_folders(command_line_sources, config_file_data),
        file_filters=get_str_list_from_config("file_filters", config_file_data, default=default_file_filters),
        work_folder=get_path_from_config("work_folder", config_file_data, default=default_work_folder),
        mutator_opts=get_dict_from_config("mutator_opts", config_file_data, default=default_mutator_opts),
        runner_opts=get_dict_from_config("runner_opts", config_file_data, default=default_runner_opts),
    )


def get_config_file_path(config_file: Optional[Path]) -> Optional[Path]:
    if config_file:
        if not config_file.is_file():
            raise PoodleInvalidInput(f"Config file not found: --config_file='{config_file}'")
        return config_file

    files = ["poodle.toml", "pyproject.toml"]  # TODO ["poodle.toml", "tox.ini", "setup.cfg", "pyproject.toml"]

    for file in files:
        path = Path(file)
        if path.is_file():
            return path

    return None


def get_config_file_data(config_file: Optional[Path]) -> dict:
    if not config_file:
        return {}

    if config_file.suffix == ".toml":
        return get_config_file_data_toml(config_file)

    # TODO tox.ini and setup.cfg
    # https://tox.wiki/en/3.24.5/config.html

    raise PoodleInvalidInput(f"Config file type not supported: --config_file='{str(config_file)}'")


def get_config_file_data_toml(config_file: Path) -> dict:
    config_data = tomllib.load(config_file.open(mode="rb"))
    config_data = config_data.get("tool", config_data)
    return config_data.get("poodle", {})


def get_source_folders(command_line_sources: Tuple[Path], config_data: dict) -> List[Path]:
    source_folders = get_path_list_from_config(
        option_name="source_folders",
        config_data=config_data,
        command_line=command_line_sources,
        default=[source for source in default_source_folders if source.is_dir()],
    )

    if not source_folders:
        raise PoodleInvalidInput("No source folder found to mutate.")

    for source in source_folders:
        if not source.is_dir():
            raise PoodleInvalidInput(f"Source '{source}' must be a folder.")

    return source_folders


def get_path_from_config(
    option_name: str,
    config_data: dict,
    default: Optional[Path] = None,
    command_line: Optional[Path] = None,
) -> Path:
    """Retrieve Config Option that should be a String.

    Retrieve highest priority value from config sources.
    """
    value, source = get_any_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not value:
        return default

    try:
        return Path(value)
    except TypeError:
        raise PoodleInvalidInput(f"{option_name} from {source} must be a valid StrPath")


def get_path_list_from_config(
    option_name: str,
    config_data: dict,
    default: List[Path] = [],
    command_line: Tuple[Path] = tuple(),
) -> Path:
    """Retrieve Config Option that should be a List of Paths.

    Retrieve highest priority value from config sources.
    If input was a single Path, return as a list of Paths.
    Convert input Iterable to List.
    """
    values, source = get_any_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not values:
        return default

    try:
        if isinstance(values, Path):
            return [values]

        if isinstance(values, str):
            return [Path(values)]

        return [Path(value) for value in values]
    except TypeError:
        raise PoodleInvalidInput(f"{option_name} from {source} must be a valid Iterable[StrPath]")


def get_str_from_config(
    option_name: str,
    config_data: dict,
    default: str = "",
    command_line: str = "",
) -> str:
    """Retrieve Config Option that should be a String.

    Retrieve highest priority value from config sources.
    """
    value, _ = get_any_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not value:
        return default

    return str(value)


def get_str_list_from_config(
    option_name: str,
    config_data: dict,
    default: List[str] = [],
    command_line: Union[str, Tuple[str]] = tuple(),
) -> List[str]:
    """Retrieve Config Option that should be a List of Strings.

    Retrieve highest priority value from config sources.
    If input was a single string, return as a list of strings.
    Convert input Iterable to List.
    """
    values, source = get_any_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not values:
        return default

    if isinstance(values, str):
        return [values]

    try:
        return [str(value) for value in values]
    except TypeError:
        raise PoodleInvalidInput(f"{option_name} from {source} must be a valid Iterable[str]")


def get_any_from_config(
    option_name: str,
    config_data: dict,
    command_line: Any,
) -> Tuple[Any, str]:
    """Retrieve Config Option of any type.

    Check sources in priority order, and return the first one found.

    Priority Order: Command Line, poodle_config.py, config file

    Returns: Identified Config value, Source Name
    """
    if command_line:
        return command_line, "Command Line"

    if hasattr(poodle_config, option_name):
        return getattr(poodle_config, option_name), "poodle_config.py"

    if option_name in config_data:
        return config_data[option_name], "config file"

    return None, None


def get_dict_from_config(
    option_name: str,
    config_data: dict,
    default: dict = {},
    command_line: dict = {},
) -> dict:
    """Merge Key-Value pairs from Config sources to a dict.

    Builds dict by starting with values from lowest priority source.
    Then 'updating' them with values from higher priority sources.

    Priority Order: Command Line, poodle_config.py, config file, defaults
    """
    option_value = default

    if option_name in config_data:
        try:
            option_value.update(config_data[option_name])
        except ValueError:
            raise PoodleInvalidInput(f"{option_name} in config file must be a valid dict")

    if hasattr(poodle_config, option_name):
        try:
            option_value.update(getattr(poodle_config, option_name))
        except ValueError:
            raise PoodleInvalidInput(f"poodle_config.{option_name} must be a valid dict")

    if command_line:
        option_value.update(command_line)

    return option_value
