# Copyright (c) 2023 WiredNerd
# SPDX-License-Identifier: MIT
import contextlib
import os
import stat
import threading
from pathlib import Path
from unittest import mock
from zipfile import ZipFile, ZipInfo

import pytest
from wcmatch import glob

from poodle import util
from poodle.data_types import Mutant, MutantTrial, PoodleWork
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def mock_logger():
    with mock.patch("poodle.util.logger") as logger:
        yield logger


def file_copy_lister_stub(config, folder):
    return [folder / config.project_name]


def test_logger():
    assert util.logger.name == "poodle.util"


class TestFilesList:
    @mock.patch("poodle.util.Path")
    def test_files_list_for_folder(self, mock_path, mock_logger):
        files = [
            Path("src/project/file_1.py"),
            Path("src/project/file_test_2.py"),
        ]
        mock_folder = mock.MagicMock()
        mock_folder.rglob.return_value = iter(files)
        mock_path.return_value = mock_folder
        in_folder = mock.MagicMock()

        assert (
            util.files_list_for_folder(
                folder=in_folder,
                match_glob="*.py",
                flags=4,
                filter_globs=["test_*.py"],
            )
            == files
        )

        mock_folder.rglob.assert_called_with("*.py", flags=4, exclude=["test_*.py"])
        mock_logger.debug.assert_any_call(
            "files_list_for_folder folder=%s, match_glob=%s filter_globs=%s",
            in_folder,
            "*.py",
            ["test_*.py"],
        )
        mock_logger.debug.assert_any_call(
            "files_list_for_folder results: folder=%s files=%s",
            in_folder,
            files,
        )

    @mock.patch("poodle.util.files_list_for_folder")
    def test_files_list_for_source_folders_file_copy_lister(self, files_list_for_folder):
        work = PoodleWork(
            config=PoodleConfigStub(
                project_name="listed.txt",
                source_folders=[Path("src"), Path("lib")],
                file_copy_lister="tests.test_util.file_copy_lister_stub",
            )
        )

        assert util.files_list_for_source_folders(work) == {
            Path("src"): [Path("src/listed.txt")],
            Path("lib"): [Path("lib/listed.txt")],
        }
        files_list_for_folder.assert_not_called()

    @mock.patch("poodle.util._unlisted_links", mock.MagicMock(return_value=[]))
    @mock.patch("poodle.util.Path")
    def test_files_list_for_source_folders(self, mock_path):
        files_1 = [
            Path("file_1.py"),
            Path("test_file_1.py"),
        ]
        files_2 = [
            Path("file_test_2.py"),
            Path("file_2_test.py"),
        ]
        mock_folder = mock.MagicMock()
        mock_folder.rglob.side_effect = [iter(files_1), iter(files_2)]
        mock_path.return_value = mock_folder

        mock_folder_1 = mock.MagicMock()
        mock_folder_2 = mock.MagicMock()

        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[mock_folder_1, mock_folder_2],
                file_copy_flags=0,
                file_copy_filters=["test_*.py", "*_test.py"],
            )
        )

        assert util.files_list_for_source_folders(work) == {
            mock_folder_1: files_1,
            mock_folder_2: files_2,
        }

        mock_path.assert_has_calls(
            [
                mock.call(mock_folder_1),
                mock.call().rglob("*", flags=0, exclude=["test_*.py", "*_test.py"]),
                mock.call(mock_folder_2),
                mock.call().rglob("*", flags=0, exclude=["test_*.py", "*_test.py"]),
            ]
        )
        mock_folder.rglob.assert_has_calls(
            [
                mock.call("*", flags=0, exclude=["test_*.py", "*_test.py"]),
                mock.call("*", flags=0, exclude=["test_*.py", "*_test.py"]),
            ]
        )

    @mock.patch("poodle.util.files_list_for_source_folders")
    @mock.patch("poodle.util.ZipFile")
    def test_create_temp_zips(self, ZipFile, files_list_for_source_folders, mock_logger):  # noqa: N803
        work_folder = mock.MagicMock()
        work_folder.__truediv__.side_effect = lambda x: Path(x)
        files_list_for_source_folders.return_value = {
            Path("example_1"): [Path("file_1.py")],
            Path("example_2"): [Path("file_2.py")],
        }
        work = PoodleWork(
            config=PoodleConfigStub(
                work_folder=work_folder,
            )
        )
        util.create_temp_zips(work)
        work_folder.mkdir.assert_called_with(parents=True, exist_ok=True)
        files_list_for_source_folders.assert_called_with(work)
        mock_logger.info.assert_has_calls(
            [
                mock.call("Creating zip file: %s", Path("src-1.zip")),
                mock.call("Adding file: %s", Path("file_1.py")),
                mock.call("Creating zip file: %s", Path("src-2.zip")),
                mock.call("Adding file: %s", Path("file_2.py")),
            ]
        )
        assert work.folder_zips == {
            Path("example_1"): Path("src-1.zip"),
            Path("example_2"): Path("src-2.zip"),
        }
        ZipFile.assert_any_call(Path("src-1.zip"), "w")
        ZipFile.assert_any_call(Path("src-2.zip"), "w")
        target_zip = ZipFile.return_value.__enter__.return_value
        target_zip.write.assert_has_calls(
            [
                mock.call(Path("file_1.py")),
                mock.call(Path("file_2.py")),
            ]
        )


class TestDynamicImport:
    def test_dynamic_import(self, mock_logger):
        runner = util.dynamic_import("poodle.runners.command_line.runner")
        import poodle.runners.command_line

        assert runner is poodle.runners.command_line.runner

        mock_logger.debug.assert_called_with("Import object: %s", "poodle.runners.command_line.runner")


class TestPrint:
    def test_pprint_str(self):
        assert util.pprint_str({"key1": "value1", "key2": "value2"}) == "{'key1': 'value1', 'key2': 'value2'}\n"

    @mock.patch("poodle.util.StringIO")
    @mock.patch("poodle.util.pprint")
    def test_pprint_str_mock(self, pprint, StringIO):  # noqa: N803
        obj = {"key1": "value1", "key2": "value2"}
        util.pprint_str(obj)
        out = StringIO.return_value
        pprint.assert_called_with(obj, stream=out, width=150)


class TestCalcTimeout:
    def test_calc_timeout(self):
        config = PoodleConfigStub(min_timeout=10, timeout_multiplier=10)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=2.01),
        }
        assert round(util.calc_timeout(config, clean_run_results), 1) == 20.1

    def test_calc_timeout_mult(self):
        config = PoodleConfigStub(min_timeout=10, timeout_multiplier=5)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=2.01),
        }
        assert round(util.calc_timeout(config, clean_run_results), 2) == round(10.05, 2)

    def test_calc_timeout_min(self):
        config = PoodleConfigStub(min_timeout=10, timeout_multiplier=10)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=0.1),
        }
        assert round(util.calc_timeout(config, clean_run_results), 1) == 10.0

    def test_calc_timeout_min_20(self):
        config = PoodleConfigStub(min_timeout=20, timeout_multiplier=10)
        clean_run_results = {
            "folder": MutantTrial(mutant=None, result=None, duration=0.1),
        }
        assert round(util.calc_timeout(config, clean_run_results), 1) == 20.0


class TestMutateLines:
    def test_mutate_lines(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=2,
            end_col_offset=13,
            text="Goodbye",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Hello World!",
            "3 Poodles are the best",
        ]
        assert util.mutate_lines(mutant, file_lines) == [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Goodbye!",
            "3 Poodles are the best",
        ]

    def test_mutate_lines_multi(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=4,
            end_col_offset=3,
            text="Goodbye, T",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Hello World!",
            "3 Poodles are the best",
            "4 Two are better than one",
        ]
        assert util.mutate_lines(mutant, file_lines) == [
            "1 The quick brown fox jumps over the lazy dog",
            "2 Goodbye, Two are better than one",
        ]


class TestUnifiedDiff:
    def test_create_unified_diff(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=2,
            end_col_offset=13,
            text="Goodbye",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog\n",
            "2 Hello World!\n",
            "3 Poodles are the best\n",
        ]
        mutant.source_file.read_text.return_value.splitlines.return_value = file_lines
        mutant.source_file.__str__.return_value = "src/example.py"
        diff_str = (
            "--- src/example.py\n"
            "+++ [Mutant] src/example.py:2\n"
            "@@ -1,3 +1,3 @@\n"
            " 1 The quick brown fox jumps over the lazy dog\n"
            "-2 Hello World!\n"
            "+2 Goodbye!\n"
            " 3 Poodles are the best\n"
        )
        assert util.create_unified_diff(mutant) == diff_str

    def test_create_unified_diff_multiline(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=3,
            end_col_offset=22,
            text="Hello Poodle!\n3 Poodles are smart",
            source_folder=mock.MagicMock(),
            source_file=mock.MagicMock(),
        )
        file_lines = [
            "1 The quick brown fox jumps over the lazy dog\n",
            "2 Hello World!\n",
            "3 Poodles are the best!\n",
        ]
        mutant.source_file.read_text.return_value.splitlines.return_value = file_lines
        mutant.source_file.__str__.return_value = "src/example.py"
        diff_str = (
            "--- src/example.py\n"
            "+++ [Mutant] src/example.py:2\n"
            "@@ -1,3 +1,3 @@\n"
            " 1 The quick brown fox jumps over the lazy dog\n"
            "-2 Hello World!\n"
            "-3 Poodles are the best!\n"
            "+2 Hello Poodle!\n"
            "+3 Poodles are smart!\n"
        )
        assert util.create_unified_diff(mutant) == diff_str

    def test_create_unified_diff_no_file(self):
        mutant = Mutant(
            mutator_name="Example",
            lineno=2,
            col_offset=2,
            end_lineno=2,
            end_col_offset=13,
            text="Goodbye",
            source_folder=mock.MagicMock(),
            source_file=None,
        )
        assert util.create_unified_diff(mutant) is None


class TestDisplayPercent:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0.0014, "0.1%"),
            (0.0016, "0.1%"),
            (0.1239, "12.3%"),
            (0.12, "12%"),
            (0.1, "10%"),
            (0.99, "99%"),
            (0.999, "99.9%"),
            (0.9999, "99.9%"),
        ],
    )
    def test_display_percent(self, value, expected):
        assert util.display_percent(value) == expected


class TestDeleteFolder:
    @pytest.fixture()
    def shutil(self):
        with mock.patch("poodle.util.shutil") as shutil:
            yield shutil

    def test_delete_folder_exists(self, shutil, mock_logger):
        folder = mock.MagicMock()
        folder.exists.return_value = True

        util.delete_folder(folder, PoodleConfigStub(skip_delete_folder=False))

        mock_logger.info.assert_called_once_with("delete %s", folder)
        shutil.rmtree.assert_called_once_with(folder)

    def test_delete_folder_exists_skip(self, shutil, mock_logger):
        folder = mock.MagicMock()
        folder.exists.return_value = True

        util.delete_folder(folder, PoodleConfigStub(skip_delete_folder=True))

        mock_logger.info.assert_not_called()
        shutil.rmtree.assert_not_called()

    def test_delete_folder_not_exists(self, shutil, mock_logger):
        folder = mock.MagicMock()
        folder.exists.return_value = False

        util.delete_folder(folder, PoodleConfigStub(skip_delete_folder=False))

        mock_logger.info.assert_not_called()
        shutil.rmtree.assert_not_called()


@pytest.mark.skipif(os.name != "posix", reason="file modes are POSIX semantics")
class TestExtractTrialFolder:
    @pytest.fixture()
    def umask_077(self):
        old = os.umask(0o077)
        yield
        os.umask(old)

    def zip_with_modes(self, folder_zip: Path, entries: dict[str, int]) -> None:
        with ZipFile(folder_zip, "w") as zip_file:
            for name, mode in entries.items():
                info = ZipInfo(name)
                info.external_attr = mode << 16
                zip_file.writestr(info, "x\n")

    @pytest.mark.usefixtures("umask_077")
    def test_extract_trial_folder_restores_modes(self, tmp_path):
        folder_zip = tmp_path / "src.zip"
        self.zip_with_modes(
            folder_zip,
            {"src/run.sh": stat.S_IFREG | 0o755, "src/ro.py": stat.S_IFREG | 0o444, "src/none.txt": 0},
        )
        run_folder = tmp_path / "run"
        run_folder.mkdir()

        with ZipFile(folder_zip) as zip_file:
            util.extract_trial_folder(zip_file, run_folder)

        assert stat.S_IMODE((run_folder / "src/run.sh").stat().st_mode) == 0o755
        assert stat.S_IMODE((run_folder / "src/ro.py").stat().st_mode) == 0o444
        assert stat.S_IMODE((run_folder / "src/none.txt").stat().st_mode) == 0o600  # no mode recorded: umask

    @pytest.mark.usefixtures("umask_077")
    def test_extract_trial_folder_modes_land_where_extractall_puts_entries(self, tmp_path):
        folder_zip = tmp_path / "src.zip"
        self.zip_with_modes(folder_zip, {"../up.sh": stat.S_IFREG | 0o755})
        run_folder = tmp_path / "run"
        run_folder.mkdir()
        outside = tmp_path / "up.sh"
        outside.write_text("x\n")
        outside.chmod(0o600)

        with ZipFile(folder_zip) as zip_file:
            util.extract_trial_folder(zip_file, run_folder)

        assert stat.S_IMODE((run_folder / "up.sh").stat().st_mode) == 0o755
        assert stat.S_IMODE(outside.stat().st_mode) == 0o600


@pytest.fixture()
def link_tree(tmp_path, monkeypatch):
    """Source folder 'src' (cwd-relative, as poodle resolves it) holding one link per rule."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg" / "mod.py").write_text("X = 1\n")
    (src / "real").mkdir()
    (src / "real" / "f.txt").write_text("f\n")
    (tmp_path / "shared" / "d").mkdir(parents=True)
    (tmp_path / "shared" / "conf.py").write_text("conf\n")
    (tmp_path / "shared" / "d" / "y.txt").write_text("y\n")
    links = {
        "src/pkg/alias.py": "mod.py",  # relative, inside
        "src/abs_alias.py": str(src / "pkg" / "mod.py"),  # absolute, inside
        "src/pkg/abs_up.txt": str(src / "real" / "f.txt"),  # absolute, inside, one level up
        "src/dir_link": "real",  # directory, inside
        "src/pkg/up": "..",  # the folder itself
        "src/loop_a": "loop_b",  # loop, inside
        "src/loop_b": "loop_a",
        "src/gen.txt": str(src / "missing.txt"),  # dangling, absolute, inside
        "src/conf.py": "../shared/conf.py",  # file, outside
        "src/abs_conf.py": str(tmp_path / "shared" / "conf.py"),  # file, outside, absolute
        "src/outdir": "../shared/d",  # directory, outside
        "src/through.txt": "outdir/y.txt",  # inside lexically, but through an omitted link
        "src/gone": "../nowhere",  # dangling, outside
    }
    for name, target in links.items():
        (tmp_path / name).symlink_to(target)
    return tmp_path


@pytest.mark.skipif(os.name != "posix", reason="symlinks are reproduced on POSIX only")
class TestTrialLinks:
    def test_trial_links(self, link_tree):
        files = [Path(name) for name in ("src/pkg/mod.py", "src/real/f.txt")]
        files += [path.relative_to(link_tree) for path in (link_tree / "src").rglob("*") if path.is_symlink()]

        links = util.trial_links(Path("src"), files)

        assert {str(path): target for path, target in links.items()} == {
            "src/pkg/alias.py": "mod.py",
            "src/abs_alias.py": "pkg/mod.py",
            "src/pkg/abs_up.txt": "../real/f.txt",
            "src/dir_link": "real",
            "src/pkg/up": "..",
            "src/loop_a": "loop_b",
            "src/loop_b": "loop_a",
            "src/gen.txt": "missing.txt",
            "src/conf.py": str(link_tree / "shared" / "conf.py"),
            "src/abs_conf.py": str(link_tree / "shared" / "conf.py"),
            "src/outdir": str(link_tree / "shared" / "d"),
            "src/through.txt": str(link_tree / "shared" / "d" / "y.txt"),
            "src/gone": str(link_tree / "nowhere"),
        }

    def test_trial_links_resolve_where_the_trial_can_follow(self, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        monkeypatch.chdir(project.parent)
        (project / "src" / "pkg").mkdir(parents=True)
        (project / "src" / "mod.py").write_text("X = 1\n")
        (project / "shared" / "d").mkdir(parents=True)
        (project / "shared" / "d" / "y.txt").write_text("y\n")
        (project / "conf.txt").write_text("c\n")
        (project / "src" / "pkg" / "up").symlink_to("..")
        (project / "src" / "outdir").symlink_to("../shared/d")
        (project / "src" / "x.py").symlink_to("../../proj/src/mod.py")  # inside, through the project name
        (project / "src" / "through.txt").symlink_to("outdir/y.txt")  # outside, through a link
        (project / "src" / "updot.txt").symlink_to("pkg/up/../conf.txt")  # "up/.." is not "": outside
        files = [Path("proj/src/mod.py"), Path("proj/src/x.py"), Path("proj/src/through.txt")]
        files += [Path("proj/src/updot.txt"), Path("proj/src/pkg/up")]  # outdir left out by a filter

        links = util.trial_links(Path("proj/src"), files)

        assert {str(path): target for path, target in links.items()} == {
            "proj/src/x.py": "mod.py",
            "proj/src/through.txt": str(project / "shared" / "d" / "y.txt"),
            "proj/src/updot.txt": str(project / "conf.txt"),
            "proj/src/pkg/up": "..",
        }

    def test_files_list_for_source_folders_lists_loops_under_excluded_directories(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "src" / "pkg" / "sub").mkdir(parents=True)
        (tmp_path / "src" / "pkg" / "sub" / "m.py").write_text("m\n")
        (tmp_path / "src" / "pkg" / "sub" / "la").symlink_to("lb")
        (tmp_path / "src" / "pkg" / "sub" / "lb").symlink_to("la")
        (tmp_path / "src" / ".hidden").mkdir()
        (tmp_path / "src" / ".hidden" / "lh").symlink_to("lh")
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[Path("src")],
                file_copy_flags=glob.GLOBSTAR | glob.NODIR,
                file_copy_filters=["pkg/*", "lb"],
            )
        )

        listed = {str(path) for path in util.files_list_for_source_folders(work)[Path("src")]}

        assert listed == {"src/pkg/sub/m.py", "src/pkg/sub/la"}  # a filter applies to a loop link at any depth

    def test_files_list_for_source_folders_lists_links(self, link_tree):
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[Path("src")],
                file_copy_flags=glob.GLOBSTAR | glob.NODIR | glob.FOLLOW,
                file_copy_filters=[],
            )
        )

        listed = {str(path) for path in util.files_list_for_source_folders(work)[Path("src")]}

        links = {str(path.relative_to(link_tree)) for path in (link_tree / "src").rglob("*") if path.is_symlink()}
        assert listed == {"src/pkg/mod.py", "src/real/f.txt"} | links  # no directory, nothing under a link

    def test_create_temp_zips_links(self, link_tree):
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[Path("src")],
                file_copy_flags=glob.GLOBSTAR | glob.NODIR,
                file_copy_filters=[],
                work_folder=link_tree / "work",
            )
        )

        util.create_temp_zips(work)

        with ZipFile(work.folder_zips[Path("src")]) as zip_file:
            entries = {
                info.filename: (stat.S_ISLNK(info.external_attr >> 16), zip_file.read(info).decode())
                for info in zip_file.infolist()
            }
        assert entries["src/pkg/alias.py"] == (True, "mod.py")
        assert entries["src/abs_alias.py"] == (True, "pkg/mod.py")
        assert entries["src/dir_link"] == (True, "real")
        assert entries["src/conf.py"] == (True, str(link_tree / "shared" / "conf.py"))
        assert entries["src/through.txt"] == (True, str(link_tree / "shared" / "d" / "y.txt"))
        assert entries["src/outdir"] == (True, str(link_tree / "shared" / "d"))
        assert entries["src/gone"] == (True, str(link_tree / "nowhere"))
        assert not [name for name in entries if name.startswith(("src/dir_link/", "src/outdir/"))]

    def test_create_temp_zips_link_to_outside_fifo(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "out").mkdir()
        fifo = tmp_path / "out" / "pipe"
        os.mkfifo(fifo)
        (tmp_path / "src" / "pipe_link").symlink_to(fifo)
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[Path("src")],
                file_copy_flags=glob.GLOBSTAR | glob.NODIR,
                file_copy_filters=[],
                work_folder=tmp_path / "work",
            )
        )

        # a copy that opens the FIFO blocks until a writer opens it: run it bounded, and release it
        copy = threading.Thread(target=util.create_temp_zips, args=(work,), daemon=True)
        copy.start()
        copy.join(5)
        hung = copy.is_alive()
        if hung:
            with contextlib.suppress(OSError):  # ENXIO: no reader is blocked on it after all
                os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))  # a writer end, closed at once: EOF
            copy.join(5)
        assert not hung

        with ZipFile(work.folder_zips[Path("src")]) as zip_file:
            entries = {
                info.filename: (stat.S_ISLNK(info.external_attr >> 16), zip_file.read(info).decode())
                for info in zip_file.infolist()
            }
        assert entries == {"src/pipe_link": (True, str(fifo))}

    def test_trial_folder_keeps_links_outside_the_folder(self, link_tree):
        (link_tree / "src" / "pkg" / "mod.py").chmod(0o750)
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[Path("src")],
                file_copy_flags=glob.GLOBSTAR | glob.NODIR,
                file_copy_filters=[],
                work_folder=link_tree / "work",
            )
        )
        util.create_temp_zips(work)
        run_folder = link_tree / "run"
        run_folder.mkdir()

        with ZipFile(work.folder_zips[Path("src")]) as zip_file:
            util.extract_trial_folder(zip_file, run_folder)

        trial = run_folder / "src"
        outside_names = ("outdir", "conf.py", "gone")
        assert all((trial / name).is_symlink() for name in outside_names)
        outside = {name: os.readlink(trial / name) for name in outside_names}  # noqa: PTH115
        assert outside == {
            "outdir": str(link_tree / "shared" / "d"),
            "conf.py": str(link_tree / "shared" / "conf.py"),
            "gone": str(link_tree / "nowhere"),
        }
        assert (trial / "outdir" / "y.txt").read_text() == "y\n"
        assert (trial / "conf.py").read_text() == "conf\n"
        assert not (trial / "gone").exists()
        inside_names = ("pkg/alias.py", "abs_alias.py", "dir_link", "pkg/up", "gen.txt")
        inside = {name: os.readlink(trial / name) for name in inside_names}  # noqa: PTH115
        assert inside == {
            "pkg/alias.py": "mod.py",
            "abs_alias.py": "pkg/mod.py",
            "dir_link": "real",
            "pkg/up": "..",
            "gen.txt": "missing.txt",
        }
        assert (trial / "abs_alias.py").read_text() == "X = 1\n"
        assert stat.S_IMODE((trial / "pkg" / "mod.py").stat().st_mode) == 0o750

    def test_create_temp_zips_link_to_filtered_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "notes.log").write_text("log\n")
        (tmp_path / "src" / "log_link.txt").symlink_to("notes.log")
        work = PoodleWork(
            config=PoodleConfigStub(
                source_folders=[Path("src")],
                file_copy_flags=glob.GLOBSTAR | glob.NODIR,
                file_copy_filters=["*.log"],
                work_folder=tmp_path / "work",
            )
        )

        util.create_temp_zips(work)

        with ZipFile(work.folder_zips[Path("src")]) as zip_file:
            entries = {info.filename: zip_file.read(info).decode() for info in zip_file.infolist()}
        assert entries == {"src/log_link.txt": "notes.log"}  # the link, not the filtered file's content

    def test_extract_trial_folder_recreates_links(self, tmp_path):
        folder_zip = tmp_path / "src.zip"
        with ZipFile(folder_zip, "w") as zip_file:
            zip_file.writestr("src/pkg/mod.py", "X = 1\n")
            link = ZipInfo("src/pkg/alias.py")
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            zip_file.writestr(link, "mod.py")
        run_folder = tmp_path / "run"
        run_folder.mkdir()

        with ZipFile(folder_zip) as zip_file:
            util.extract_trial_folder(zip_file, run_folder)

        alias = run_folder / "src" / "pkg" / "alias.py"
        assert alias.is_symlink()
        assert os.readlink(alias) == "mod.py"  # noqa: PTH115 - the target text is what is under test
        assert alias.read_text() == "X = 1\n"
