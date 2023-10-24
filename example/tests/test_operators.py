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


def test_exponentiation():
    assert exponentiation(2, 10) == 1024


def test_floor_division():
    assert floor_division(14, 4) == 3
