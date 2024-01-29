"""Mutate Functions and Calls."""

from __future__ import annotations

import ast
from copy import deepcopy

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Mutator Class."""
    plugin_manager.register(LambdaMutator(), "LambdaMutator")


class LambdaMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Return from Lambdas."""

    mutator_name = "Lambda"
    mutants: list[FileMutation]

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Replace body of Lambda with None or empty string."""
        if isinstance(node.body, ast.Constant) and node.body.value is None:
            mut = deepcopy(node)
            mut.body = ast.Constant("")
            self.mutants.append(self.create_file_mutation(mut, ast.unparse(mut)))
        else:
            mut = deepcopy(node)
            mut.body = ast.Constant(None)
            self.mutants.append(self.create_file_mutation(mut, ast.unparse(mut)))
