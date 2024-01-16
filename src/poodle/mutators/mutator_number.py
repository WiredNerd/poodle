"""Mutate Number Values."""

from __future__ import annotations

import ast

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Number Mutator Class."""
    plugin_manager.register(NumberMutator(), "NumberMutator")


class NumberMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Numbers."""

    # Various Keywords:
    # complex   3j
    # int       3, 0o3 0x3, 0b11
    # float     3.0

    mutator_name = "Number"
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
        """Increase and Decrease values."""
        if isinstance(node.value, bool):
            return
        if isinstance(node.value, int):
            self.mutants.append(self.create_file_mutation(node, str(node.value + 1)))
            self.mutants.append(self.create_file_mutation(node, str(node.value - 1)))
        if isinstance(node.value, complex):
            self.mutants.append(self.create_file_mutation(node, str(node.value + 1j)))
            self.mutants.append(self.create_file_mutation(node, str(node.value - 1j)))
        if isinstance(node.value, float):
            if node.value == 0:
                self.mutants.append(self.create_file_mutation(node, str(1.0)))
            else:
                self.mutants.append(self.create_file_mutation(node, str(node.value * 2)))
                self.mutants.append(self.create_file_mutation(node, str(node.value / 2)))
