from typing import Any

from constants import str_value


def function_call():
    str_value()


def dict_subscript(input_dict: dict[Any, Any], key):
    return input_dict[key]


def list_item(input_list: list[Any], idx):
    return input_list[idx]
