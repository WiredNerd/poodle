"""Mutate Constant Values."""

from __future__ import annotations

import ast

from poodle.data_types import FileMutation, Mutator


class NumberMutator(ast.NodeVisitor, Mutator):
    """Mutate Numbers."""

    # Various Keywords:
    # complex   3j
    # int       3, 0o3 0x3, 0b11
    # float     3.0

    mutator_name = "Number"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Constant(self, node: ast.Constant) -> None:
        """Increase and Decrease values."""
        if isinstance(node.value, bool):
            return
        if isinstance(node.value, int):
            self.mutants.append(self.create_file_mutation(node, str(node.value + 1)))
            self.mutants.append(self.create_file_mutation(node, str(node.value - 1)))
        if isinstance(node.value, complex):
            self.mutants.append(self.create_file_mutation(node, str(node.value + 1j)))
            self.mutants.append(self.create_file_mutation(node, str(node.value - 1j)))
        if isinstance(node.value, float):
            if node.value == 0:
                self.mutants.append(self.create_file_mutation(node, str(1.0)))
            else:
                self.mutants.append(self.create_file_mutation(node, str(node.value * 2)))
                self.mutants.append(self.create_file_mutation(node, str(node.value / 2)))


class StringMutator(ast.NodeVisitor, Mutator):
    """Mutate String."""

    mutator_name = "String"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants

    def visit_Constant(self, node: ast.Constant) -> None:
        """Mutate String values."""
        if isinstance(node.parent, ast.Expr):  # type: ignore [attr-defined]
            return

        if isinstance(node.value, str):
            node.value = f"XX{node.value}XX"
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))


class KeywordMutator(ast.NodeVisitor, Mutator):
    """Mutate Keywords.

    continue, break, False, True, None
    """

    mutator_name = "Keyword"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants

    def visit_Break(self, node: ast.Break) -> None:
        """Replace break with continue."""
        self.mutants.append(self.create_file_mutation(node, "continue"))

    def visit_Continue(self, node: ast.Continue) -> None:
        """Replace continue with break."""
        self.mutants.append(self.create_file_mutation(node, "break"))

    def visit_Constant(self, node: ast.Constant) -> None:
        """Replace True, False, and None."""
        if self.is_annotation(node):
            return

        if node.value is True:
            self.mutants.append(self.create_file_mutation(node, "False"))
        if node.value is False:
            self.mutants.append(self.create_file_mutation(node, "True"))
        if node.value is None:
            self.mutants.append(self.create_file_mutation(node, "' '"))
