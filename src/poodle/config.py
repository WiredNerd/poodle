import tomllib
from contextlib import suppress
from pathlib import Path
from typing import Optional

from poodle import PoodleInvalidInput
from poodle.data import PoodleConfig

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

poodle_config: any = None
with suppress(ImportError):
    import poodle_config  # type: ignore

default_source_folders = [Path("src"), Path("lib")]
default_file_filters = ["^test_", "_test$"]
default_work_folder = Path(".poodle-temp")
default_mutator_opts = {}
default_runner_opts = {"command_line": "pytest --assert=plain -o pythonpath="}


def build_config(source: tuple[str], config_file: str):
    config_file_path = get_config_file_path(config_file)
    config_file_data = get_config_file_data(config_file_path)

    return PoodleConfig(
        config_file=config_file_path,
        source_folders=get_source_folders(source, config_file_data),
        file_filters=default_file_filters,
        work_folder=default_work_folder,
        mutator_opts=get_mutator_opts_from_config(config_file_data),
        runner_opts=get_runner_opts_from_config(config_file_data),
    )


def get_config_file_path(config_file: str) -> Optional[Path]:
    if config_file:
        path = Path(config_file)
        if path.is_file():
            return path
        else:
            raise PoodleInvalidInput(f"Config file not found: --{config_file=}")

    files = ["poodle.toml", "pyproject.toml"]  # TODO tox.ini and setup.cfg

    for file in files:
        path = Path(file)
        if path.is_file():
            return path

    return None


def get_config_file_data(config_file: Optional[Path]) -> dict:
    if not config_file:
        return {}

    if config_file.suffix == ".toml":
        return get_config_file_toml(config_file)

    # TODO tox.ini and setup.cfg
    # https://tox.wiki/en/3.24.5/config.html

    raise PoodleInvalidInput(f"Config file type not supported: --config_file='{str(config_file)}'")


def get_config_file_toml(config_file: Path):
    config_data = tomllib.load(config_file.open(mode="rb"))
    config_data = config_data.get("tool", config_data)
    return config_data.get("poodle", {})


def get_source_folders(source, config_file):
    source_folders = get_source_folders_from_config(source, config_file)

    if not source_folders:
        raise PoodleInvalidInput("No source folder found to mutate.")

    for source in source_folders:
        if not source.is_dir():
            raise PoodleInvalidInput("Source must be a folder.", str(source))

    return source_folders


def get_source_folders_from_config(sources: tuple[str], config_file: dict) -> list[Path]:
    if sources:
        return [Path(source) for source in sources]

    if hasattr(poodle_config, "source_folders") and poodle_config.source_folders:
        try:
            return [Path(source) for source in iter(poodle_config.source_folders)]
        except TypeError:
            raise PoodleInvalidInput("poodle_config.source_folders must be of type Iterable[PathStr]")

    if "source_folders" in config_file:
        try:
            return [Path(source) for source in iter(config_file["source_folders"])]
        except TypeError:
            raise PoodleInvalidInput("source_folders in config file must be of type Iterable[str]")

    return [source for source in default_source_folders if source.is_dir()]


def get_mutator_opts_from_config(config_file: dict) -> dict:
    mutator_opts = default_mutator_opts

    if "mutator_opts" in config_file:
        try:
            mutator_opts.update(config_file["mutator_opts"])
        except ValueError:
            raise PoodleInvalidInput("mutator_opts in config file must be a valid dict")

    if hasattr(poodle_config, "mutator_opts"):
        try:
            mutator_opts.update(poodle_config.mutator_opts)
        except ValueError:
            raise PoodleInvalidInput("poodle_config.mutator_opts must be a valid dict")

    return mutator_opts


def get_runner_opts_from_config(config_file: dict) -> dict:
    runner_opts = default_runner_opts

    if "runner_opts" in config_file:
        try:
            runner_opts.update(config_file["runner_opts"])
        except ValueError:
            raise PoodleInvalidInput("runner_opts in config file must be a valid dict")

    if hasattr(poodle_config, "runner_opts"):
        try:
            runner_opts.update(poodle_config.runner_opts)
        except ValueError:
            raise PoodleInvalidInput("poodle_config.runner_opts must be a valid dict")

    return runner_opts
