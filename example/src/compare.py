from __future__ import annotations


def equals(a, b):
    return a == b


def less_than(a, b):
    return a < b


def less_than_equal(a, b):
    return a <= b


def greater_than(a, b):
    return a > b


def greater_than_equal(a, b):
    return a >= b


def value_is(a, b):
    return a is b


def value_is_not(a, b):
    return a is not b


def value_in(a, b):
    return a in b


def value_not_in(a, b):
    return a not in b


def is_a_or_b(a, b):
    return a or b


def is_a_and_b(a, b):
    return a and b
