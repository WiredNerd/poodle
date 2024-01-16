"""Mutate Functions and Calls."""

from __future__ import annotations

import ast

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Mutator Class."""
    plugin_manager.register(SubscriptMutator(), "SubscriptMutator")


class SubscriptMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Calls to Dict or Array with Subscript."""

    mutator_name = "Subscript"
    mutants: list[FileMutation]

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []
        
        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Replace Call to retrieve from Dict or Array with None."""
        if self.is_annotation(node):
            return
        
        self.mutants.append(self.create_file_mutation(node, "None"))
