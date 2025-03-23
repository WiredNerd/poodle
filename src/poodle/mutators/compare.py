"""Mutate Comparison Operators."""

from __future__ import annotations

import ast
import re
from copy import deepcopy
from typing import ClassVar

from poodle.data_types import FileMutation, Mutator


class ComparisonMutator(ast.NodeVisitor, Mutator):
    """Mutate Comparison Operators."""

    # https://docs.python.org/3/library/ast.html#ast.Compare
    # https://www.w3schools.com/python/python_operators.asp
    # ast.Eq      ==
    # ast.NotEq   !=
    # ast.Lt      <
    # ast.LtE     <=
    # ast.Gt      >
    # ast.GtE     >=
    # ast.Is      is
    # ast.IsNot   is not
    # ast.In      in
    # ast.NotIn   not in
    # ast.Or      or
    # ast.And     and

    type_map: ClassVar[dict[type, list[type]]] = {
        ast.Eq: [ast.NotEq],
        ast.NotEq: [ast.Eq],
        ast.Lt: [ast.GtE, ast.LtE],
        ast.LtE: [ast.Gt, ast.Lt],
        ast.Gt: [ast.LtE, ast.GtE],
        ast.GtE: [ast.Lt, ast.Gt],
        ast.Is: [ast.IsNot],
        ast.IsNot: [ast.Is],
        ast.In: [ast.NotIn],
        ast.NotIn: [ast.In],
        ast.Or: [ast.And],
        ast.And: [ast.Or],
    }

    mutator_name = "Compare"

    def __init__(self, *args, **kwargs) -> None:
        """Initialize and read settings."""
        super().__init__(*args, **kwargs)
        self.mutants: list[FileMutation] = []

        self.filter_patterns: list[str] = [
            r"__name__ == '__main__'",
        ]

        self.filter_patterns += self.config.mutator_opts.get("compare_filters", [])

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all Comparisons and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants

    def visit_Compare(self, node: ast.Compare) -> None:
        """Identify replacement Operations and create Mutants."""
        text = ast.unparse(node)
        for pattern in self.filter_patterns:
            if re.match(pattern, text):
                return

        for idx, op in enumerate(node.ops):
            for new_op in self.type_map[type(op)]:
                mut = deepcopy(node)
                mut.ops[idx] = new_op()
                self.mutants.append(self.create_file_mutation(node, ast.unparse(mut)))

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Identify replacement Operations and create Mutants."""
        if self.is_annotation(node) or type(node.op) not in self.type_map:
            return

        text = ast.unparse(node)
        for pattern in self.filter_patterns:
            if re.match(pattern, text):
                return

        for new_op in self.type_map[type(node.op)]:
            mut = deepcopy(node)
            mut.op = new_op()
            self.mutants.append(self.create_file_mutation(node, ast.unparse(mut)))
