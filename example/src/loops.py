def sum_of_evens(values: list[int]):
    sum = 0
    for value in values:
        if value % 2 > 0:
            continue
        sum += value
    return sum


def everything_before(values: list[int], before: int):
    out = []
    for value in values:
        if value == before:
            break
        out.append(value)
    return out
