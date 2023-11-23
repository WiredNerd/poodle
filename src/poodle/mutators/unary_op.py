"""Mutate Unary Operations."""

from __future__ import annotations

import ast

from ..data_types import FileMutation, Mutator


class UnaryOperationMutator(ast.NodeVisitor, Mutator):
    """Mutate Unary Operations."""

    # Unary Operators as of Python 3.12:
    # https://docs.python.org/3/library/ast.html#ast.UnaryOp
    # https://www.w3schools.com/python/python_operators.asp
    # ast.UAdd      +
    # ast.USub      -
    # ast.Not       not
    # ast.Invert    ~

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all Unary Operations and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if isinstance(node.op, ast.UAdd):
            self.mutants.append(self.create_mutant(node, ast.unparse(ast.UnaryOp(op=ast.USub(), operand=node.operand))))
        if isinstance(node.op, ast.USub):
            self.mutants.append(self.create_mutant(node, ast.unparse(ast.UnaryOp(op=ast.UAdd(), operand=node.operand))))
        if isinstance(node.op, (ast.Not, ast.Invert)):
            self.mutants.append(self.create_mutant(node, ast.unparse(node.operand)))

    def create_mutant(self, node: ast.UnaryOp, text: str):
        """Create Mutants."""
        return FileMutation(
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno or node.lineno,
            end_col_offset=node.end_col_offset or node.col_offset,
            text=text,
        )
