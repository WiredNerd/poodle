"""Mutate Constant Values."""

from __future__ import annotations

import ast
from copy import deepcopy

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register String Mutator Class."""
    plugin_manager.register(StringMutator(), "StringMutator")


class StringMutator(ast.NodeVisitor, MutatorBase):
    """Mutate String."""

    mutator_name = "String"
    mutants: list[FileMutation]

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Constant(self, node: ast.Constant) -> None:
        """Mutate String values."""
        if isinstance(node.parent, ast.Expr):  # type: ignore [attr-defined]
            return

        if isinstance(node.value, str):
            mut = deepcopy(node)
            mut.value = f"XX{mut.value}XX"
            self.mutants.append(self.create_file_mutation(mut, ast.unparse(mut)))
