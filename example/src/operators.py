from __future__ import annotations


def addition(x, y):
    return x + y


def subtraction(x, y):
    return x - y


def multiplication(x, y):
    return x * y


def division(x, y):
    return x / y


def modulus(x, y):
    return x % y


def floor_division(x, y):
    return x // y


def exponentiation(x, y):
    return x**y


def left_shift(x, y):
    return x << y


def right_shift(x, y):
    return x >> y


def bit_or(x, y) -> str | int:
    return x | y


def bit_xor(x, y):
    return x ^ y


def bit_and(x, y):
    return x & y


def unary_add(x):
    return +x


def unary_sub(x):
    return -x


def unary_not(x):
    return not x


def unary_invert(x):
    return ~x
