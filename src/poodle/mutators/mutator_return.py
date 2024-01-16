"""Mutate Functions and Calls."""

from __future__ import annotations

import ast
from copy import deepcopy

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Comparison Mutator Class."""
    plugin_manager.register(ReturnMutator(), "ReturnMutator")


class ReturnMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Return from Functions."""

    mutator_name = "Return"
    mutants: list[FileMutation]

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Return(self, node: ast.Return) -> None:
        """Replace return statements with return None or Return empty string."""
        if node.value is None:
            return
        mut = deepcopy(node)
        if isinstance(mut.value, ast.Constant) and mut.value.value is None:
            mut.value = ast.Constant("")
            self.mutants.append(self.create_file_mutation(mut, ast.unparse(mut)))
        else:
            mut.value = ast.Constant(None)
            self.mutants.append(self.create_file_mutation(mut, ast.unparse(mut)))
