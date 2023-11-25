import functools
from typing import Any

from constants import str_value


def function_call():
    str_value()


def dict_subscript(input_dict: dict[Any, Any], key):
    return input_dict[key]


def list_item(input_list: list[Any], idx):
    return input_list[idx]


example_lambda = lambda x, y: x + y
example_lambda_none = lambda x, y: None


def example_returns(x):
    if x:
        return x
    else:
        return None


def add_one(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs) + 1

    return wrapper


def times_two(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs) * 2

    return wrapper


class ExampleClass:
    @staticmethod
    def static_method(a):
        return a

    @classmethod
    def class_method(cls, a):
        return a

    @times_two
    @add_one
    @times_two
    def return_four(self):
        return 4
