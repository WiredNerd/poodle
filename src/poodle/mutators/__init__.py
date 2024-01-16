"""Collection of Mutators."""

from . import (
    mutator_bool_op,
    mutator_compare,
    mutator_decorator,
    mutator_function_call,
    mutator_keyword,
    mutator_lambda,
    mutator_loop_break,
    mutator_number,
    mutator_operation,
    mutator_return,
    mutator_string,
    mutator_subscript,
    mutator_unary_op,
)

mutator_plugins = [
    mutator_bool_op,
    mutator_compare,
    mutator_decorator,
    mutator_function_call,
    mutator_keyword,
    mutator_lambda,
    mutator_loop_break,
    mutator_number,
    mutator_operation,
    mutator_return,
    mutator_string,
    mutator_subscript,
    mutator_unary_op,
]
