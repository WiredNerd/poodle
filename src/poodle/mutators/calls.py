"""Mutate ...."""

from __future__ import annotations

import ast
from _ast import FunctionDef, Lambda
from copy import deepcopy
from typing import Any

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


class LambdaReturnMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Lambda(self, node: ast.Lambda) -> None:
        if isinstance(node.body, ast.Constant) and node.body.value is None:
            node.body = ast.Constant("")
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))
        else:
            node.body = ast.Constant(None)
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))


class ReturnMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Return(self, node: ast.Return) -> None:
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            node.value = ast.Constant("")
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))
        else:
            node.value = ast.Constant(None)
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))


class DecoratorMutator(ast.NodeVisitor, Mutator):
    """Mutate ..."""

    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.decorator_list:
            decorator_list = node.decorator_list
            for idx in range(0,len(node.decorator_list)):
                mod_list = deepcopy(decorator_list)
                mod_list.pop(idx)
                node.decorator_list = mod_list
                self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))
