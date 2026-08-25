import time

from cython_engine.python_order_book import Order, OrderBook
from cython_engine.order_book import CythonOrder, CythonOrderBook


NUM_ORDERS = 10_000


def benchmark_python():
    start = time.perf_counter()

    for i in range(NUM_ORDERS):
        book = OrderBook()

        sell = Order(
            order_id=1,
            price=100.0,
            quantity=50,
            side="SELL",
            timestamp=1,
        )

        buy = Order(
            order_id=2,
            price=100.0,
            quantity=50,
            side="BUY",
            timestamp=2,
        )

        book.add_order(sell)

        # Use the Python reference matching method
        book.match_order(buy)

    return time.perf_counter() - start


def benchmark_cython():
    start = time.perf_counter()

    for i in range(NUM_ORDERS):
        book = CythonOrderBook()

        sell = CythonOrder(
            1,
            100.0,
            50,
            False,
            1,
        )

        buy = CythonOrder(
            2,
            100.0,
            50,
            True,
            2,
        )

        book.add_order(sell)
        book.match_order(buy)

    return time.perf_counter() - start


if __name__ == "__main__":

    python_time = benchmark_python()
    cython_time = benchmark_cython()

    speedup = python_time / cython_time

    print("\n========== CHRONOSMATCH BENCHMARK ==========")

    print(f"Orders:          {NUM_ORDERS}")
    print(f"Python time:     {python_time:.6f} seconds")
    print(f"Cython time:     {cython_time:.6f} seconds")
    print(f"Speedup:         {speedup:.2f}x")

    print("=============================================\n")