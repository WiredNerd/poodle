from __future__ import annotations

from augassign import *


def test_addition_assign():
    assert addition_assign(4, 6) == 10


def test_subtraction_assign():
    assert subtraction_assign(6, 4) == 2


def test_multiplication():
    assert multiplication_assign(4, 3) == 12


def test_division():
    assert division_assign(12, 4) == 3


def test_modulus():
    assert modulus_assign(14, 4) == 2


def test_floor_division():
    assert floor_division_assign(14, 4) == 3


def test_exponentiation():
    assert exponentiation_assign(2, 10) == 1024


def test_left_shift():
    assert left_shift_assign(3, 2) == 12


def test_right_shift():
    assert right_shift_assign(15, 2) == 3


def test_bit_or():
    assert bit_or_assign(5, 12) == 13


def test_bit_xor():
    assert bit_xor_assign(5, 12) == 9


def test_bit_and():
    assert bit_and_assign(5, 12) == 4
