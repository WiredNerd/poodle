"""Mutate Constant Values."""

from __future__ import annotations

import ast

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Keyword Mutator Class."""
    plugin_manager.register(KeywordMutator(), "KeywordMutator")


class KeywordMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Keywords False, True, and None."""

    mutator_name = "Keyword"

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

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
