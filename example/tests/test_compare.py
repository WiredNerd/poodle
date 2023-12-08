from compare import *


def test_equals():
    assert equals(3, 3) is True


def test_less_than():
    assert less_than(2, 3) is True
    assert less_than(2, 2) is False


def test_less_than_equal():
    assert less_than_equal(2, 3) is True
    assert less_than_equal(2, 2) is True


def test_greater_than():
    assert greater_than(3, 2) is True
    assert greater_than(2, 2) is False


def test_greater_than_equal():
    assert greater_than_equal(3, 2) is True
    assert greater_than_equal(2, 2) is True


def test_value_is():
    assert value_is(True, True) is True


def test_value_is_not():
    assert value_is_not(True, False) is True


def test_value_in():
    assert value_in(1, [1, 2, 3]) is True


def test_value_not_in():
    assert value_not_in(4, [1, 2, 3]) is True


def test_is_a_or_b():
    assert is_a_or_b(True, True) is True
    assert is_a_or_b(True, False) is True
    assert is_a_or_b(False, True) is True
    assert is_a_or_b(False, False) is False


def test_is_a_and_b():
    assert is_a_and_b(True, True) is True
    assert is_a_and_b(True, False) is False
    assert is_a_and_b(False, True) is False
    assert is_a_and_b(False, False) is False
