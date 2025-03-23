from __future__ import annotations


def is_none(a) -> None | bool:
    return a is None


def is_true(a) -> None | bool:
    return a is True


def is_false(a) -> None | bool:
    return a is False


def int_constant_n1():
    return -1


def int_constant_0():
    return 0


def int_constant_1():
    return 1


def int_constant_n1j():
    return -1j


def int_constant_0j():
    return 0j


def int_constant_1j():
    return 1j


def float_constant_small():
    return 5e-5


def float_constant_neg_small():
    return -5e-5


def float_constant_large():
    return 5e5


def float_constant_neg_large():
    return -5e5


def float_constant():
    return 5.5


def float_constant_neg():
    return -5.5


def str_value():
    """docstring"""
    return "こんにちは"
