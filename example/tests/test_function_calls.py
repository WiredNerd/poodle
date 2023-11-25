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
