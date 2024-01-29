"""Mutate Functions and Calls."""

from __future__ import annotations

import ast

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Mutator Class."""
    plugin_manager.register(FunctionCallMutator(), "FunctionCallMutator")


class FunctionCallMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Function Calls."""

    mutator_name = "FuncCall"
    mutants: list[FileMutation]

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Call(self, node: ast.Call) -> None:
        """Replace Function calls with None."""
        self.mutants.append(self.create_file_mutation(node, "None"))
