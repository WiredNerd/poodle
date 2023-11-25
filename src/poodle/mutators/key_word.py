"""Mutate ...."""

from __future__ import annotations

import ast

from ..data_types import FileMutation, Mutator


class KeywordMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    # Various Keywords:

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Break(self, node: ast.Break) -> None:
        self.mutants.append(self.create_file_mutation(node, "continue"))

    def visit_Continue(self, node: ast.Break) -> None:
        self.mutants.append(self.create_file_mutation(node, "break"))

    def visit_Constant(self, node: ast.Constant) -> None:
        if node.value is True:
            self.mutants.append(self.create_file_mutation(node, "False"))
        if node.value is False:
            self.mutants.append(self.create_file_mutation(node, "True"))
        if node.value is None:
            self.mutants.append(self.create_file_mutation(node, "''"))
