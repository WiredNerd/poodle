from loops import *


def test_sum_of_evens():
    assert sum_of_evens(list(range(0, 7))) == 12


def test_everything_before():
    assert everything_before(list(range(0, 7)), 3) == [0, 1, 2]
