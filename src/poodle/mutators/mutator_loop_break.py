"""Mutate Constant Values."""

from __future__ import annotations

import ast

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register LoopBreak Mutator Class."""
    plugin_manager.register(LoopBreakMutator(), "LoopBreakMutator")


class LoopBreakMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Keywords continue and break."""

    mutator_name = "LoopBreak"

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Break(self, node: ast.Break) -> None:
        """Replace break with continue."""
        self.mutants.append(self.create_file_mutation(node, "continue"))

    def visit_Continue(self, node: ast.Continue) -> None:
        """Replace continue with break."""
        self.mutants.append(self.create_file_mutation(node, "break"))
