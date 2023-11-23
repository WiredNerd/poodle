from operators import *


def test_addition():
    assert addition(4, 6) == 10


def test_subtraction():
    assert subtraction(6, 4) == 2


def test_multiplication():
    assert multiplication(4, 3) == 12


def test_division():
    assert division(12, 4) == 3


def test_modulus():
    assert modulus(14, 4) == 2


def test_floor_division():
    assert floor_division(14, 4) == 3


def test_exponentiation():
    assert exponentiation(2, 10) == 1024


def test_left_shift():
    assert left_shift(3, 2) == 12


def test_right_shift():
    assert right_shift(15, 2) == 3


def test_bit_or():
    assert bit_or(5, 12) == 13


def test_bit_xor():
    assert bit_xor(5, 12) == 9


def test_bit_and():
    assert bit_and(5, 12) == 4


def test_unary_add():
    assert unary_add(4) == 4


def test_unary_sub():
    assert unary_sub(5) == -5


def test_unary_not():
    assert unary_not(True) is False


def test_unary_invert():
    assert unary_invert(4) == -5
