"""Mutate ...."""

from __future__ import annotations

import ast

from ..data_types import FileMutation, Mutator


class FunctionCallMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Call(self, node: ast.Call) -> None:
        self.mutants.append(self.create_file_mutation(node, "None"))


class DictArrayCallMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Skip if Subscript is part of annotation
        if hasattr(node.parent, "annotation") and node.parent.annotation is node:
            return

        self.mutants.append(self.create_file_mutation(node, "None"))
