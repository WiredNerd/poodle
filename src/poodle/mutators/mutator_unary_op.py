"""Mutate Unary Operations."""

from __future__ import annotations

import ast

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Unary Op Mutator Class."""
    plugin_manager.register(UnaryOperationMutator(), "UnaryOperationMutator")


class UnaryOperationMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Unary Operations."""

    # https://docs.python.org/3/library/ast.html#ast.UnaryOp
    # https://www.w3schools.com/python/python_operators.asp
    # ast.UAdd      +
    # ast.USub      -
    # ast.Not       not
    # ast.Invert    ~

    mutator_name = "UnaryOp"

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all Unary Operations and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        """Create mutations."""
        if isinstance(node.op, ast.UAdd):
            self.mutants.append(
                self.create_file_mutation(node, ast.unparse(ast.UnaryOp(op=ast.USub(), operand=node.operand))),
            )
        if isinstance(node.op, ast.USub):
            self.mutants.append(
                self.create_file_mutation(node, ast.unparse(ast.UnaryOp(op=ast.UAdd(), operand=node.operand))),
            )
        if isinstance(node.op, (ast.Not, ast.Invert)):
            self.mutants.append(self.create_file_mutation(node, ast.unparse(node.operand)))
