"""Mutate ...."""

from __future__ import annotations

import ast

from ..data_types import FileMutation, Mutator


class NumberMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    # Various Keywords:
    # complex   3j
    # int       3, 0o3 0x3, 0b11
    # float     3.0

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, int):
            self.mutants.append(self.create_file_mutation(node, str(node.value + 1)))
            self.mutants.append(self.create_file_mutation(node, str(node.value - 1)))
        if isinstance(node.value, complex):
            self.mutants.append(self.create_file_mutation(node, str(node.value + 1j)))
            self.mutants.append(self.create_file_mutation(node, str(node.value - 1j)))
        if isinstance(node.value, float):
            if node.value == 0.0:
                self.mutants.append(self.create_file_mutation(node, str(1.0)))
            else:
                self.mutants.append(self.create_file_mutation(node, str(node.value * 2)))
                self.mutants.append(self.create_file_mutation(node, str(node.value / 2)))


class StringMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.parent, ast.Expr):
            return

        if isinstance(node.value, str):
            self.mutants.append(self.create_file_mutation(node, "XX" + node.value + "XX"))
