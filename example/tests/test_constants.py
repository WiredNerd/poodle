from __future__ import annotations

from constants import *


def test_is_none():
    assert is_none(None) is True
    assert is_none(True) is False


def test_is_true():
    assert is_true(True) is True
    assert is_true(None) is False


def test_is_false():
    assert is_false(False) is True
    assert is_false(None) is False


def test_int_constant_n1():
    assert int_constant_n1() == -1


def test_int_constant_0():
    assert int_constant_0() == 0


def test_int_constant_1():
    assert int_constant_1() == 1


def test_int_constant_n1j():
    assert int_constant_n1j() == -1j


def test_int_constant_0j():
    assert int_constant_0j() == 0j


def test_int_constant_1j():
    assert int_constant_1j() == 1j


def test_float_constant_small():
    assert float_constant_small() == 5e-5


def test_float_constant_neg_small():
    assert float_constant_neg_small() == -5e-5


def test_float_constant_large():
    assert float_constant_large() == 5e5


def test_float_constant_neg_large():
    assert float_constant_neg_large() == -5e5


def test_float_constant():
    assert float_constant() == 5.5


def test_float_constant_neg():
    assert float_constant_neg() == -5.5


def test_str_value():
    assert str_value() == "こんにちは"
