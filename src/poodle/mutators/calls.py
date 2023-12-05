"""Mutate Functions and Calls."""

from __future__ import annotations

import ast
from copy import deepcopy

from poodle.data_types import FileMutation, Mutator


class FunctionCallMutator(ast.NodeVisitor, Mutator):
    """Mutate Function Calls."""

    mutator_name = "FuncCall"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Call(self, node: ast.Call) -> None:
        """Replace Function calls with None."""
        self.mutants.append(self.create_file_mutation(node, "None"))


class DictArrayCallMutator(ast.NodeVisitor, Mutator):
    """Mutate Calls to Dict or Array."""

    mutator_name = "DictArray"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Replace Call to retrieve from Dict or Array with None."""
        if self.is_annotation(node):
            return

        self.mutants.append(self.create_file_mutation(node, "None"))


class LambdaReturnMutator(ast.NodeVisitor, Mutator):
    """Mutate Return from Lambdas."""

    mutator_name = "Lambda"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Replace body of Lambda with None or empty string."""
        if isinstance(node.body, ast.Constant) and node.body.value is None:
            node.body = ast.Constant("")
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))
        else:
            node.body = ast.Constant(None)
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))


class ReturnMutator(ast.NodeVisitor, Mutator):
    """Mutate Return from Functions."""

    mutator_name = "Return"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Return(self, node: ast.Return) -> None:
        """Replace return statements with return None or Return empty string."""
        if node.value is None:
            return
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            node.value = ast.Constant("")
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))
        else:
            node.value = ast.Constant(None)
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node)))


class DecoratorMutator(ast.NodeVisitor, Mutator):
    """Mutate Decorators."""

    mutator_name = "Decorator"
    mutants: list[FileMutation]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Remove Decorators on Function Definitions."""
        if node.decorator_list:
            for idx in range(len(node.decorator_list)):
                new_node = deepcopy(node)
                new_node.decorator_list.pop(idx)
                self.mutants.append(self.create_file_mutation(node, ast.unparse(new_node)))
