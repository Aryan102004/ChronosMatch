import time

from cython_engine.python_order_book import Order, OrderBook
from cython_engine.order_book import CythonOrder, CythonOrderBook


NUM_ROUNDS = 10_000


def python_full_match():
    for i in range(NUM_ROUNDS):
        book = OrderBook()

        sell = Order(
            i * 2 + 1,
            100.0,
            50,
            "SELL",
            i * 2 + 1
        )

        buy = Order(
            i * 2 + 2,
            100.0,
            50,
            "BUY",
            i * 2 + 2
        )

        book.add_order(sell)
        book.match_order(buy)


def cython_full_match():
    for i in range(NUM_ROUNDS):
        book = CythonOrderBook()

        sell = CythonOrder(
            i * 2 + 1,
            100.0,
            50,
            False,
            i * 2 + 1
        )

        buy = CythonOrder(
            i * 2 + 2,
            100.0,
            50,
            True,
            i * 2 + 2
        )

        book.add_order(sell)
        book.match_order(buy)


def python_partial_fill():
    for i in range(NUM_ROUNDS):
        book = OrderBook()

        sell = Order(1, 100.0, 50, "SELL", 1)
        buy = Order(2, 100.0, 80, "BUY", 2)

        book.add_order(sell)
        book.match_order(buy)


def cython_partial_fill():
    for i in range(NUM_ROUNDS):
        book = CythonOrderBook()

        sell = CythonOrder(
            1,
            100.0,
            50,
            False,
            1
        )

        buy = CythonOrder(
            2,
            100.0,
            80,
            True,
            2
        )

        book.add_order(sell)
        book.match_order(buy)


def python_multiple_levels():
    for i in range(NUM_ROUNDS):
        book = OrderBook()

        book.add_order(Order(1, 100.0, 50, "SELL", 1))
        book.add_order(Order(2, 101.0, 30, "SELL", 2))
        book.add_order(Order(3, 102.0, 40, "SELL", 3))

        buy = Order(4, 101.0, 70, "BUY", 4)

        book.match_order(buy)


def cython_multiple_levels():
    for i in range(NUM_ROUNDS):
        book = CythonOrderBook()

        book.add_order(
            CythonOrder(1, 100.0, 50, False, 1)
        )

        book.add_order(
            CythonOrder(2, 101.0, 30, False, 2)
        )

        book.add_order(
            CythonOrder(3, 102.0, 40, False, 3)
        )

        buy = CythonOrder(
            4,
            101.0,
            70,
            True,
            4
        )

        book.match_order(buy)

def python_mixed_flow():
    for i in range(NUM_ROUNDS):
        book = OrderBook()

        book.add_order(
            Order(
                i * 4 + 1,
                100.0,
                50,
                "SELL",
                i * 4 + 1
            )
        )

        book.add_order(
            Order(
                i * 4 + 2,
                99.0,
                40,
                "BUY",
                i * 4 + 2
            )
        )

        book.match_order(
            Order(
                i * 4 + 3,
                100.0,
                30,
                "BUY",
                i * 4 + 3
            )
        )

        book.match_order(
            Order(
                i * 4 + 4,
                99.0,
                20,
                "SELL",
                i * 4 + 4
            )
        )


def cython_mixed_flow():
    for i in range(NUM_ROUNDS):
        book = CythonOrderBook()

        book.add_order(
            CythonOrder(
                i * 4 + 1,
                100.0,
                50,
                False,
                i * 4 + 1
            )
        )

        book.add_order(
            CythonOrder(
                i * 4 + 2,
                99.0,
                40,
                True,
                i * 4 + 2
            )
        )

        book.match_order(
            CythonOrder(
                i * 4 + 3,
                100.0,
                30,
                True,
                i * 4 + 3
            )
        )

        book.match_order(
            CythonOrder(
                i * 4 + 4,
                99.0,
                20,
                False,
                i * 4 + 4
            )
        )
def run_benchmark(name, python_func, cython_func):
    python_start = time.perf_counter()
    python_func()
    python_time = time.perf_counter() - python_start

    cython_start = time.perf_counter()
    cython_func()
    cython_time = time.perf_counter() - cython_start

    speedup = python_time / cython_time

    print(
        f"{name:<25}"
        f"{python_time:>12.6f}"
        f"{cython_time:>12.6f}"
        f"{speedup:>10.2f}x"
    )


if __name__ == "__main__":

    print()
    print("=" * 65)
    print("           CHRONOSMATCH PYTHON vs CYTHON")
    print("=" * 65)

    print(f"Rounds per scenario: {NUM_ROUNDS}")
    print()

    print(
        f"{'Scenario':<25}"
        f"{'Python (s)':>12}"
        f"{'Cython (s)':>12}"
        f"{'Speedup':>10}"
    )

    print("-" * 65)

    run_benchmark(
        "Full Match",
        python_full_match,
        cython_full_match
    )

    run_benchmark(
        "Partial Fill",
        python_partial_fill,
        cython_partial_fill
    )

    run_benchmark(
        "Multiple Levels",
        python_multiple_levels,
        cython_multiple_levels
    )
    run_benchmark(
        "Mixed Order Flow",
        python_mixed_flow,
        cython_mixed_flow
    )
    print("=" * 65)
    print()