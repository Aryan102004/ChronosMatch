"""
ChronosMatch IPC Benchmark.

Measures the throughput of the mmap ring buffer.
"""

import os
import time

from ipc import RingBuffer, Order, BUY, SELL


IPC_FILE = "benchmark_chronosmatch.ipc"

CAPACITY = 100_000


def run_benchmark(
    number_of_orders: int = 100_000,
):
    """Benchmark writing and reading orders."""

    # Remove previous benchmark file
    if os.path.exists(IPC_FILE):
        os.remove(IPC_FILE)

    ring_buffer = RingBuffer(
        path=IPC_FILE,
        capacity=CAPACITY,
    )

    ring_buffer.create()

    print("=" * 65)
    print("ChronosMatch IPC Benchmark")
    print("=" * 65)
    print(f"Orders       : {number_of_orders:,}")
    print(f"Buffer size  : {CAPACITY:,} slots")
    print()

    # ------------------------------------------------
    # WRITE BENCHMARK
    # ------------------------------------------------

    print("Starting producer benchmark...")

    write_start = time.perf_counter_ns()

    written = 0

    for i in range(number_of_orders):

        order = Order(
            order_id=i + 1,
            price=245.50 + (i % 100) * 0.01,
            quantity=(i % 1000) + 1,
            side=BUY if i % 2 == 0 else SELL,
            timestamp_ns=time.perf_counter_ns(),
        )

        if ring_buffer.write(order):
            written += 1

    write_end = time.perf_counter_ns()

    write_time_ns = (
        write_end - write_start
    )

    # ------------------------------------------------
    # READ BENCHMARK
    # ------------------------------------------------

    print("Starting consumer benchmark...")

    read_start = time.perf_counter_ns()

    consumed = 0

    while True:

        order = ring_buffer.read()

        if order is None:
            break

        consumed += 1

    read_end = time.perf_counter_ns()

    read_time_ns = (
        read_end - read_start
    )

    # ------------------------------------------------
    # CALCULATE RESULTS
    # ------------------------------------------------

    write_time_sec = (
        write_time_ns / 1_000_000_000
    )

    read_time_sec = (
        read_time_ns / 1_000_000_000
    )

    write_rate = (
        written / write_time_sec
        if write_time_sec > 0
        else 0
    )

    read_rate = (
        consumed / read_time_sec
        if read_time_sec > 0
        else 0
    )

    print()
    print("=" * 65)
    print("Benchmark Results")
    print("=" * 65)

    print(
        f"Orders requested : {number_of_orders:,}"
    )

    print(
        f"Orders written   : {written:,}"
    )

    print(
        f"Orders consumed  : {consumed:,}"
    )

    print(
        f"Orders lost      : "
        f"{written - consumed:,}"
    )

    print()

    print(
        f"Write time       : "
        f"{write_time_sec:.6f} sec"
    )

    print(
        f"Read time        : "
        f"{read_time_sec:.6f} sec"
    )

    print()

    print(
        f"Write throughput : "
        f"{write_rate:,.0f} orders/sec"
    )

    print(
        f"Read throughput  : "
        f"{read_rate:,.0f} orders/sec"
    )

    print("=" * 65)

    ring_buffer.close()

    # Remove benchmark file
    if os.path.exists(IPC_FILE):
        os.remove(IPC_FILE)


if __name__ == "__main__":

    run_benchmark(
        number_of_orders=100_000
    )