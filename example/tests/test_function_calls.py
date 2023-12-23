from __future__ import annotations

from unittest import mock

from function_calls import *


@mock.patch("function_calls.str_value")
def test_function_call(example_function):
    function_call()
    example_function.assert_called()


def test_dict_subscript():
    a = {
        "a": 1,
        "b": 2,
    }
    assert dict_subscript(a, "a") == 1


def test_list_item():
    assert list_item([1, 2, 3], 1) == 2


def test_example_lambda():
    assert example_lambda(1, 2) == 3


def test_example_lambda_none():
    assert example_lambda_none(1, 2) is None


def test_example_returns():
    assert example_returns(True) is True
    assert example_returns(False) is None


def test_add_one():
    @add_one
    def func():
        return 3

    assert func() == 4


def test_times_two():
    @times_two
    def func():
        return 3

    assert func() == 6


def test_return_four():
    c = ExampleClass()
    assert c.return_four() == 18


def test_static_method():
    assert ExampleClass.static_method(4) == 4
    c = ExampleClass()
    assert c.static_method(4) == 4


def test_class_method():
    assert ExampleClass.class_method(5) == 5
    c = ExampleClass()
    assert c.class_method(5) == 5
