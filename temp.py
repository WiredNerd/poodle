import itertools
import time
from multiprocessing import Manager, Pool


def calculate_worker(x, y, counter):
    # time.sleep(0.1)
    counter.value = counter.value + 1
    # print("worker", x, y)
    return x + y


if __name__ == "__main__":
    pool = Pool()

    with Manager() as manager:
        counter = manager.Value(int, 0)

        ranges = [(i, i + 1, counter) for i in range(1, 100)]

        results = pool.starmap_async(
            calculate_worker,
            ranges,
        )

        while not results.ready():
            time.sleep(0.1)
            print("waiting...", counter.value, flush=True)

    print("Results", results.get(), flush=True)
