from unittest import mock

import pytest

from poodle import PoodleInputError, mutate
from poodle.data_types import FileMutation, Mutant, Mutator, PoodleWork
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def logger_mock():
    with mock.patch("poodle.mutate.logger") as logger_mock:
        yield logger_mock


def file_mutation(mutator_name, lineno, end_lineno):
    return FileMutation(
        mutator_name=mutator_name,
        lineno=lineno,
        col_offset=0,
        end_lineno=end_lineno,
        end_col_offset=0,
        text="",
    )


class FakeMutator(Mutator):
    mutator_name = "FakeMutator"

    def create_mutations(self, *_, **__) -> list[FileMutation]:
        return []


def fake_mutator(*_, **__) -> list[FileMutation]:
    return []


class TestInit:
    @mock.patch("poodle.mutate.builtin_mutators")
    def test_initialize_mutators(self, builtin_mutators):
        config = PoodleConfigStub(skip_mutators=["m2"], add_mutators=["tests.test_mutate.fake_mutator"])
        work = PoodleWork(config)
        m1 = FakeMutator(config, echo=mock.MagicMock())
        m2 = FakeMutator(config, echo=mock.MagicMock())
        m3 = FakeMutator(config, echo=mock.MagicMock())
        builtin_mutators.items.return_value = [("m1", m1), ("m2", m2), ("m3", m3)]
        assert mutate.initialize_mutators(work) == [m1, m3, fake_mutator]

    def test_initialize_mutator_str_class(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        mutator = mutate.initialize_mutator(work, "tests.test_mutate.FakeMutator")
        logger_mock.debug.assert_called_with("tests.test_mutate.FakeMutator")
        assert isinstance(mutator, FakeMutator)
        assert not isinstance(mutator, type)
        assert mutator.config == config
        assert mutator.echo == work.echo

    def test_initialize_mutator_str_func(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        assert mutate.initialize_mutator(work, "tests.test_mutate.fake_mutator") == fake_mutator
        logger_mock.debug.assert_called_with("tests.test_mutate.fake_mutator")

    def test_initialize_mutator_class(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        mutator = mutate.initialize_mutator(work, FakeMutator)
        logger_mock.debug.assert_called_with(FakeMutator)
        assert isinstance(mutator, FakeMutator)
        assert not isinstance(mutator, type)
        assert mutator.config == config
        assert mutator.echo == work.echo

    def test_initialize_mutator_obj(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        mutator = FakeMutator(config, echo=mock.MagicMock())
        assert mutate.initialize_mutator(work, mutator) == mutator
        logger_mock.debug.assert_called_with(mutator)

    def test_initialize_mutator_func(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        assert mutate.initialize_mutator(work, fake_mutator) == fake_mutator
        logger_mock.debug.assert_called_with(fake_mutator)

    def test_initialize_mutator_invalid_error(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        with pytest.raises(
            PoodleInputError,
            match=(
                "^Unable to create mutator '3' of type=<class 'int'>. "
                "Expected String, Callable, Mutator subclass or Mutator subclass instance.$"
            ),
        ):
            mutate.initialize_mutator(work, 3)
        logger_mock.debug.assert_called_with(3)

    def test_initialize_mutator_import_error(self, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        with pytest.raises(
            PoodleInputError,
            match="^Import failed for mutator 'fake_mutator'$",
        ):
            mutate.initialize_mutator(work, "fake_mutator")
        logger_mock.debug.assert_called_with("fake_mutator")


class TestCreateMutants:
    @mock.patch("poodle.mutate.get_target_files")
    @mock.patch("poodle.mutate.create_mutants_for_file")
    def test_create_mutants_for_all_mutators(self, create_mutants_for_file, get_target_files):
        config = PoodleConfigStub()
        work = PoodleWork(config)

        get_target_files.return_value = {
            "example_1": ["file_1.py", "file_2.py"],
            "example_2": ["file_3.py", "file_4.py"],
        }

        def mock_create_mutants_for_file(work, folder, file):  # noqa: ARG001
            return [mock.MagicMock(folder=folder, file=file)]

        create_mutants_for_file.side_effect = mock_create_mutants_for_file

        out = mutate.create_mutants_for_all_mutators(work)

        get_target_files.assert_called_with(work)
        create_mutants_for_file.assert_has_calls(
            [
                mock.call(work, "example_1", "file_1.py"),
            ]
        )

        assert [(mock_out.folder, mock_out.file) for mock_out in out] == [
            ("example_1", "file_1.py"),
            ("example_1", "file_2.py"),
            ("example_2", "file_3.py"),
            ("example_2", "file_4.py"),
        ]

    @mock.patch("poodle.mutate.files_list_for_folder")
    def test_get_target_files_only(self, files_list_for_folder, logger_mock):
        files_list_for_folder.side_effect = [
            ["example1.py"],
            ["example2.py"],
            [],
            [],
        ]

        folder1 = mock.MagicMock()
        folder2 = mock.MagicMock()

        config = PoodleConfigStub(
            only_files=["example1.py", "example2.py"],
            file_flags=0,
            source_folders=[folder1, folder2],
        )
        work = PoodleWork(config)

        assert mutate.get_target_files(work) == {
            folder1: ["example1.py", "example2.py"],
            folder2: [],
        }

        logger_mock.debug.assert_called_with(
            "get_target_files source_folders=%s only_files=%s file_filters=%s",
            work.config.source_folders,
            work.config.only_files,
            work.config.source_folders,
        )

        files_list_for_folder.assert_has_calls(
            [
                mock.call(folder=folder1, match_glob="example1.py", flags=0, filter_globs=[]),
                mock.call(folder=folder1, match_glob="example2.py", flags=0, filter_globs=[]),
                mock.call(folder=folder2, match_glob="example1.py", flags=0, filter_globs=[]),
                mock.call(folder=folder2, match_glob="example2.py", flags=0, filter_globs=[]),
            ]
        )

    @mock.patch("poodle.mutate.files_list_for_folder")
    def test_get_target_files(self, files_list_for_folder):
        config = PoodleConfigStub(file_filters=["test.*.py"], file_flags=0, source_folders=["example_1", "example_2"])
        work = PoodleWork(config)

        files_list_for_folder.side_effect = [
            ["file_1.py", "file_2.py"],
            ["file_3.py", "file_4.py"],
        ]

        assert mutate.get_target_files(work) == {
            "example_1": ["file_1.py", "file_2.py"],
            "example_2": ["file_3.py", "file_4.py"],
        }

        files_list_for_folder.assert_has_calls(
            [
                mock.call(folder="example_1", match_glob="*.py", flags=0, filter_globs=["test.*.py"]),
                mock.call(folder="example_2", match_glob="*.py", flags=0, filter_globs=["test.*.py"]),
            ]
        )

    @mock.patch("poodle.mutate.ast")
    @mock.patch("poodle.mutate.deepcopy")
    def test_create_mutants_for_file(self, deepcopy, ast, logger_mock):
        config = PoodleConfigStub()
        work = PoodleWork(config)
        folder = mock.MagicMock()
        file = mock.MagicMock()

        parsed_ast = ast.parse.return_value
        file_lines = [
            "1 # nomut",
            "2",
        ]

        file.read_text.return_value.splitlines.return_value = file_lines

        def deepcopy_mock(obj):
            if obj == parsed_ast:
                return deepcopy.parsed_ast
            if obj == file_lines:
                return deepcopy.file_lines
            return deepcopy.other

        deepcopy.side_effect = deepcopy_mock

        mutator_1 = mock.MagicMock()
        file_mutants_1 = [file_mutation("Example", 1, 1), file_mutation("Example", 2, 2)]
        mutator_1.return_value = file_mutants_1

        mutator_2 = mock.MagicMock(spec=Mutator)
        file_mutants_2 = [file_mutation("Other", 1, 1), file_mutation("Other", 2, 2)]
        mutator_2.create_mutations.return_value = file_mutants_2

        work.mutators = [mutator_1, mutator_2]

        out_mutants = mutate.create_mutants_for_file(work, folder, file)

        logger_mock.debug.assert_called_with("Create Mutants for file %s", file)
        file.read_bytes.assert_called_once_with()
        file.read_text.assert_called_once_with("utf-8")
        ast.parse.assert_called_with(file.read_bytes.return_value, file)
        mutator_1.assert_called_with(config=config, parsed_ast=deepcopy.parsed_ast, file_lines=deepcopy.file_lines)
        mutator_2.create_mutations.assert_called_with(parsed_ast=deepcopy.parsed_ast, file_lines=deepcopy.file_lines)

        assert out_mutants == [
            Mutant(
                mutator_name="Example",
                lineno=2,
                col_offset=0,
                end_lineno=2,
                end_col_offset=0,
                text="",
                source_folder=folder,
                source_file=file,
            ),
            Mutant(
                mutator_name="Other",
                lineno=2,
                col_offset=0,
                end_lineno=2,
                end_col_offset=0,
                text="",
                source_folder=folder,
                source_file=file,
            ),
        ]


class TestFilter:
    def test_parse_filters(self):
        file_lines = [
            "1",
            "2 # pragma: no mutate",
            "3 # pragma: no mutate # type: ignore",
            "4 # nomut",
            "5 # nomut: Example",
            "6 # nomut: Example # type: ignore",
            "7 # nomut Example",
            "8 # nomut: Example1,Example2",
            "9 # nomut: Example1, Example2 # pragma: no mutate",
        ]
        assert mutate.parse_filters(file_lines) == {
            2: {"all"},
            3: {"all"},
            4: {"all"},
            5: {"example"},
            6: {"example"},
            7: {"example"},
            8: {"example1", "example2"},
            9: {"example1", "example2", "all"},
        }

    def test_parse_filters_start_end(self):
        file_lines = [
            "1",
            "2 # nomut: start",
            "3",
            "4 # nomut: end",
            "5",
            "6",
            "7",
            "8 # nomut: start",
            "9 # nomut: Example1, Example2",
        ]
        assert mutate.parse_filters(file_lines) == {
            2: {"all"},
            3: {"all"},
            4: {"all"},
            8: {"all"},
            9: {"all"},
        }

    def test_parse_filters_on_off(self):
        file_lines = [
            "1",
            "2 # nomut: on",
            "3",
            "4 # nomut: off",
            "5",
            "6",
            "7",
            "8 # nomut: on",
            "9 # nomut: Example1, Example2",
        ]
        assert mutate.parse_filters(file_lines) == {
            2: {"all"},
            3: {"all"},
            4: {"all"},
            8: {"all"},
            9: {"all"},
        }

    def test_add_filter(self):
        line_filters = {}
        mutate.add_line_filter(line_filters, 3, "all")
        assert line_filters == {3: {"all"}}
        mutate.add_line_filter(line_filters, 3, "Example")
        assert line_filters == {3: {"all", "example"}}
        mutate.add_line_filter(line_filters, 4, "Example")
        assert line_filters == {3: {"all", "example"}, 4: {"example"}}
        mutate.add_line_filter(line_filters, 5, "")
        assert line_filters == {3: {"all", "example"}, 4: {"example"}, 5: {"all"}}

    @pytest.mark.parametrize(
        ("mutation_args", "mutators", "expected"),
        [
            # all
            (("Example", 3, 3), {"all", "other"}, True),
            (("Example", 2, 3), {"all", "other"}, True),
            (("Example", 3, 4), {"all", "other"}, True),
            (("Example", 2, 4), {"all", "other"}, True),
            (("Example", 4, 5), {"all", "other"}, False),
            (("Example", 1, 2), {"all", "other"}, False),
            # match
            (("Example", 3, 3), {"example", "other"}, True),
            (("Example", 2, 3), {"example", "other"}, True),
            (("Example", 3, 4), {"example", "other"}, True),
            (("Example", 2, 4), {"example", "other"}, True),
            (("Example", 4, 5), {"example", "other"}, False),
            (("Example", 1, 2), {"example", "other"}, False),
            # no match
            (("Example", 3, 3), {"other", "other2"}, False),
            (("Example", 2, 3), {"other", "other2"}, False),
            (("Example", 3, 4), {"other", "other2"}, False),
            (("Example", 2, 4), {"other", "other2"}, False),
            (("Example", 4, 5), {"other", "other2"}, False),
            (("Example", 1, 2), {"other", "other2"}, False),
        ],
    )
    def test_is_filtered(self, mutation_args, mutators, expected):
        file_mutant = file_mutation(mutation_args[0], mutation_args[1], mutation_args[2])
        line_filters = {3: mutators}

        assert mutate.is_filtered(line_filters, file_mutant) is expected
