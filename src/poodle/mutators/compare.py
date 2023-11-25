"""Mutate Comparison Operations."""

from __future__ import annotations

import ast
from _ast import BoolOp
from copy import deepcopy
from typing import Any

from ..data_types import FileMutation, Mutator


class ComparisonMutator(ast.NodeVisitor, Mutator):
    """Mutate Unary Operations."""

    # Unary Operators as of Python 3.12:
    # https://docs.python.org/3/library/ast.html#ast.Compare
    # https://www.w3schools.com/python/python_operators.asp
    # ast.Eq      ==
    # ast.Lt      <
    # ast.LtE     <=
    # ast.Gt      >
    # ast.GtE     >=
    # ast.Is      is
    # ast.IsNot   is not
    # ast.In      in
    # ast.NotIn   not in

    type_map = {
        ast.Eq: [ast.NotEq],
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

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all Comparisons and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Compare(self, node: ast.Compare) -> None:
        if ast.unparse(node) in ("__name__ == '__main__'"):
            return

        for idx, op in enumerate(node.ops):
            for new_op in self.type_map[type(op)]:
                mut = deepcopy(node)
                mut.ops[idx] = new_op()
                self.mutants.append(self.create_file_mutation(node, ast.unparse(mut)))

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        for new_op in self.type_map[type(node.op)]:
            mut = deepcopy(node)
            mut.op = new_op()
            self.mutants.append(self.create_file_mutation(node, ast.unparse(mut)))
