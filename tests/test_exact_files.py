# Copyright (c) 2026 Poodle contributors
"""Literal target selection must not discover archived copies recursively."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from wcmatch import glob

from poodle import PoodleInputError, cli, config, mutate
from poodle.data_types import MutantTrialResult, PoodleWork
from poodle.run import run_mutant_trial
from poodle.util import create_temp_zips
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture(autouse=True)
def isolate_python_configuration(monkeypatch):
    monkeypatch.setattr(config, "poodle_config", None)


@pytest.fixture()
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in [
        "pkg/item.py",
        "pkg/[literal].py",
        "pkg/l.py",
        "extensionless",
        ".scratch/archive/pkg/item.py",
        "worktrees/branch/pkg/item.py",
        "unrelated/nested/pkg/item.py",
        "pkg/test_skip.py",
    ]:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("value = 10\n")
    return tmp_path


def selection_config(*, roots=None, exact=None, only=None):
    configured = PoodleConfigStub(
        source_folders=[Path()] if roots is None else roots,
        only_files=[] if only is None else only,
        file_flags=glob.GLOBSTAR | glob.NODIR | glob.DOTGLOB,
        file_filters=["test_*.py", ".scratch/**", "worktrees/**"],
        file_copy_flags=glob.GLOBSTAR | glob.NODIR | glob.DOTGLOB,
        file_copy_filters=["native-work/**"],
        work_folder=Path("native-work"),
        skip_mutators=["all"],
        add_mutators=["Number"],
        mutator_opts={},
        echo_enabled=False,
        echo_no_color=True,
    )
    # Exercise native discovery on the old release rather than failing at an
    # unsupported constructor argument before it can inspect real files.
    configured.exact_files = [] if exact is None else exact
    return configured


def built_config(path=None, *, only=()):
    return config.build_config((Path(),), path, 3, 0, 1, (), only, (), None, None, None)


def test_default_field_preserves_old_constructor_and_is_not_shared():
    first, second = PoodleConfigStub(), PoodleConfigStub()
    left, right = getattr(first, "exact_files", None), getattr(second, "exact_files", None)
    assert left == right == []
    left.append("one.py")
    assert right == []


def test_exact_literals_deduplicate_and_use_first_containing_root_for_native_trials(project):
    configured = selection_config(
        roots=[Path("pkg"), Path()],
        exact=["pkg/item.py", "./pkg/item.py", "pkg/[literal].py", "extensionless"],
    )
    configured.file_filters = ["**"]
    work = PoodleWork(configured)
    targets = mutate.get_target_files(work)
    assert targets == {
        Path("pkg"): [Path("pkg/item.py"), Path("pkg/[literal].py")],
        Path(): [Path("extensionless")],
    }
    work.mutators = mutate.initialize_mutators(work)
    mutants = mutate.create_mutants_for_all_mutators(work)
    assert {m.source_file for m in mutants} == {Path("pkg/item.py"), Path("pkg/[literal].py"), Path("extensionless")}
    assert all(not m.source_file.is_absolute() for m in mutants)
    original = (project / "pkg/item.py").read_text()
    selected = next(m for m in mutants if m.source_file == Path("pkg/item.py"))
    create_temp_zips(work)
    observed = []

    def inspect_trial(*, run_folder, mutant, **_):
        observed.append((run_folder / mutant.source_file).read_text())
        return MutantTrialResult(found=False, reason_code=MutantTrialResult.RC_NOT_FOUND)

    result = run_mutant_trial(
        configured,
        work.echo,
        work.folder_zips[selected.source_folder],
        selected,
        "exact-proof",
        inspect_trial,
        5,
    )
    assert result.result.reason_code == MutantTrialResult.RC_NOT_FOUND
    assert len(observed) == 1
    assert observed[0] != original
    assert (project / "pkg/item.py").read_text() == original


def test_toml_exact_paths_are_relative_to_discovery_cwd_not_config_folder(project):
    settings = project / "settings"
    settings.mkdir()
    path = settings / "poodle.toml"
    path.write_text('[tool.poodle]\nexact_files=["pkg/item.py"]\n')
    configured = built_config(path)
    assert getattr(configured, "exact_files", None) == ["pkg/item.py"]
    assert mutate.get_target_files(PoodleWork(configured)) == {Path(): [Path("pkg/item.py")]}


@pytest.mark.usefixtures("project")
def test_python_configuration_supplies_exact_files(monkeypatch):
    monkeypatch.setattr(config, "poodle_config", SimpleNamespace(exact_files=["pkg/item.py"]))
    configured = built_config()
    assert getattr(configured, "exact_files", None) == ["pkg/item.py"]
    assert mutate.get_target_files(PoodleWork(configured)) == {Path(): [Path("pkg/item.py")]}


@pytest.mark.parametrize("legacy", ["only", "filters"])
@pytest.mark.usefixtures("project")
def test_empty_exact_list_keeps_legacy_globs_and_filters(legacy):
    configured = selection_config(only=["pkg/item.py"] if legacy == "only" else [])
    targets = mutate.get_target_files(PoodleWork(configured))[Path()]
    if legacy == "only":
        assert set(targets) == {
            Path("pkg/item.py"),
            Path(".scratch/archive/pkg/item.py"),
            Path("worktrees/branch/pkg/item.py"),
            Path("unrelated/nested/pkg/item.py"),
        }
    else:
        assert Path("pkg/item.py") in targets
        assert Path("pkg/test_skip.py") not in targets
        assert not any(str(path).startswith((".scratch/", "worktrees/")) for path in targets)


@pytest.mark.usefixtures("project")
def test_nonempty_exact_files_conflicts_with_only_globs():
    configured = selection_config(exact=["pkg/item.py"], only=["pkg/item.py"])
    with pytest.raises(PoodleInputError):
        mutate.get_target_files(PoodleWork(configured))


def test_cli_only_cannot_silently_override_exact_configuration(project, monkeypatch):
    path = project / "poodle.toml"
    path.write_text('[tool.poodle]\nexact_files=["pkg/item.py"]\n')

    def discover(configured):
        mutate.get_target_files(PoodleWork(configured))

    monkeypatch.setattr(cli.core, "main_process", discover)
    result = CliRunner().invoke(cli.main, ["-c", str(path), "--only", "pkg/item.py", "."])
    assert result.exit_code != 0
    assert isinstance(result.exception, PoodleInputError) or "exact_files" in result.output


@pytest.mark.parametrize(
    "invalid",
    ["empty", "absolute", "traversal", "missing", "directory", "outside_roots", "absolute_root", "traversal_root"],
)
def test_unsafe_exact_targets_are_refused_before_discovery(project, invalid):
    configured = selection_config(exact=["pkg/item.py"])
    if invalid == "empty":
        configured.exact_files = [""]
    elif invalid == "absolute":
        configured.exact_files = [str(project / "pkg/item.py")]
    elif invalid == "traversal":
        configured.exact_files = ["pkg/../pkg/item.py"]
    elif invalid == "missing":
        configured.exact_files = ["pkg/missing.py"]
    elif invalid == "directory":
        configured.exact_files = ["pkg"]
    elif invalid == "outside_roots":
        configured.source_folders = [Path("unrelated")]
    elif invalid == "absolute_root":
        configured.source_folders = [project]
    else:
        configured.source_folders = [Path("../outside")]
    before = (project / "pkg/item.py").read_bytes()
    with pytest.raises(PoodleInputError):
        mutate.get_target_files(PoodleWork(configured))
    assert (project / "pkg/item.py").read_bytes() == before


@pytest.mark.parametrize("component", ["file", "directory"])
def test_exact_selection_refuses_file_and_directory_symlinks(project, component):
    if component == "file":
        (project / "alias.py").symlink_to(project / "pkg/item.py")
        name = "alias.py"
    else:
        (project / "linked").symlink_to(project / "pkg", target_is_directory=True)
        name = "linked/item.py"
    configured = selection_config(exact=[name])
    with pytest.raises(PoodleInputError):
        mutate.get_target_files(PoodleWork(configured))
