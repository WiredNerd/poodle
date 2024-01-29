import functools
from typing import Callable
from unittest import mock


class DecoratorMock:
    def __init__(self, decorator=mock.MagicMock()):
        self.decorator = decorator

    def __call__(self, *args, **kwargs):
        def decorator(f: Callable):
            self.decorator(f.__name__, *args, **kwargs)

            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                return f(*args, **kwargs)

            return decorated_function

        return decorator
