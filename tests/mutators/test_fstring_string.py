# Copyright (c) 2026 Poodle contributors
"""Keep f-string fragments distinct from real string expressions."""

import ast
from dataclasses import asdict
from pathlib import Path
from unittest import mock

import pytest

from poodle.data_types import Mutant
from poodle.mutators.constant import StringMutator
from poodle.util import mutate_lines


@pytest.mark.parametrize(
    "source",
    [
        "result = f'literal only'",
        "result = f'prefix {value} suffix'",
        "result = f'{{escaped}} {value}'",
        "result = rf'raw\\path {value}'",
        'result = f"""first\n{value}\nlast"""',
        "result = f'prefix {value!r:>8}'",
        "result = f\"outer {f'inner {value}'}\"",
        "result = f'café {value}'",
    ],
    ids=["literal", "prefix-suffix", "escaped-braces", "raw", "triple", "conversion", "nested", "unicode"],
)
def test_literal_fragments_are_not_ordinary_string_mutation_sites(source):
    mutator = StringMutator(config=mock.MagicMock(mutator_opts={}), echo=mock.MagicMock())
    assert mutator.create_mutations(ast.parse(source)) == []


@pytest.mark.parametrize(
    ("source", "expected", "output"),
    [
        (
            "result = f\"prefix {'value'} suffix\"",
            "result = f\"prefix {'XXvalueXX'} suffix\"",
            "prefix XXvalueXX suffix",
        ),
        ("result = f\"{value:{'>8'}}\"", "result = f\"{value:{'XX>8XX'}}\"", None),
        (
            'result = f"outer {f\'{str(1)}\'}" + "tail"',
            'result = f"outer {f\'{str(1)}\'}" + "XXtailXX"',
            "outer 1XXtailXX",
        ),
        ("result = f'''outer {f\"{'value'}\"}'''", "result = f'''outer {f\"{'XXvalueXX'}\"}'''", "outer XXvalueXX"),
        ("result = f\"{dict(key='value')['key']}\"", None, None),
    ],
    ids=[
        "replacement-string",
        "nested-format-field",
        "ordinary-sibling",
        "nested-expression",
        "two-expression-strings",
    ],
)
def test_real_expression_strings_remain_native_semantic_mutations(tmp_path, source, expected, output):
    original = tmp_path / "original.py"
    original.write_text(source)
    mutator = StringMutator(config=mock.MagicMock(mutator_opts={}), echo=mock.MagicMock())
    mutations = mutator.create_mutations(ast.parse(source))
    expected_sources = (
        [expected]
        if expected is not None
        else [
            "result = f\"{dict(key='XXvalueXX')['key']}\"",
            "result = f\"{dict(key='value')['XXkeyXX']}\"",
        ]
    )
    assert len(mutations) == len(expected_sources)
    actual = []
    for index, mutation in enumerate(mutations):
        native = Mutant(**asdict(mutation), source_folder=Path(), source_file=Path("original.py"))
        changed = "".join(mutate_lines(native, source.splitlines(keepends=True)))
        trial = tmp_path / f"trial-{index}.py"
        trial.write_text(changed)
        compile(changed, str(trial), "exec")
        actual.append(ast.dump(ast.parse(changed)))
        if output is not None:
            namespace = {"value": "x"}
            exec(compile(changed, str(trial), "exec"), namespace)  # noqa: S102
            assert namespace["result"] == output
    assert sorted(actual) == sorted(ast.dump(ast.parse(item)) for item in expected_sources)
    assert original.read_text() == source


def test_docstrings_still_have_no_string_mutations():
    mutator = StringMutator(config=mock.MagicMock(mutator_opts={}), echo=mock.MagicMock())
    assert mutator.create_mutations(ast.parse('"""module documentation"""')) == []
