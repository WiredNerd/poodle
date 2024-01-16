"""Mutate Functions and Calls."""

from __future__ import annotations

import ast
from copy import deepcopy

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Boolean Op Mutator Class."""
    plugin_manager.register(DecoratorMutator(), "DecoratorMutator")


class DecoratorMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Function Definitions by removing Decorators, one at a time."""

    mutator_name = "Decorator"
    mutants: list[FileMutation]

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all FunctionDef nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Remove Decorators on Function Definitions."""
        if node.decorator_list:
            for idx in range(len(node.decorator_list)):
                new_node = deepcopy(node)
                new_node.decorator_list.pop(idx)
                self.mutants.append(self.create_file_mutation(node, self.unparse_indent(new_node, new_node.col_offset)))
