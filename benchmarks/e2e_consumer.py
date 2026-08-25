"""
ChronosMatch End-to-End Consumer.

Reads orders from the mmap ring buffer, processes them through
the Cython matching engine, and measures IPC latency and
matching-engine throughput.
"""

import os
import time

from ipc import RingBuffer
from cython_engine.matching_engine import CythonMatchingEngine


IPC_FILE = "e2e_chronosmatch.ipc"

BUFFER_CAPACITY = 100_000


def percentile(values, percentile_value):
    """Calculate a percentile from a sorted list."""

    if not values:
        return 0

    index = int(
        len(values) * percentile_value / 100
    )

    index = min(
        index,
        len(values) - 1
    )

    return values[index]


def wait_for_ipc():
    """Wait until the producer creates the IPC file."""

    print("Waiting for IPC buffer...")

    while not os.path.exists(IPC_FILE):
        time.sleep(0.1)

    print("IPC buffer detected.")


def run_consumer():

    wait_for_ipc()

    ring_buffer = RingBuffer(
        path=IPC_FILE,
        capacity=BUFFER_CAPACITY,
    )

    ring_buffer.open()

    expected = ring_buffer.get_expected_orders()

    engine = CythonMatchingEngine()

    print("=" * 65)
    print("ChronosMatch E2E Consumer")
    print("=" * 65)

    print(
        f"Expected orders : {expected:,}"
    )

    print(
        "Cython engine   : ENABLED"
    )

    print(
        "Latency measurement: ENABLED"
    )

    print()

    start_time = time.perf_counter()

    consumed = 0
    trades_generated = 0

    latencies_ns = []

    last_display = start_time

    while True:

        order = ring_buffer.read()

        if order is not None:

            # Capture receive timestamp immediately
            # after reading the IPC record.
            receive_time_ns = (
                time.perf_counter_ns()
            )

            latency_ns = (
                receive_time_ns
                - order.timestamp_ns
            )

            if latency_ns >= 0:
                latencies_ns.append(
                    latency_ns
                )

            # IPC BUY = 1
            # IPC SELL = 2
            is_buy = order.side == 1

            # Send the order to the Cython
            # matching engine.
            trades = engine.match_order(
                order.order_id,
                order.price,
                order.quantity,
                is_buy,
                order.timestamp_ns,
            )

            trades_generated += len(trades)

            consumed += 1

        else:

            # Producer has finished and all expected
            # orders have been consumed.
            if (
                ring_buffer.is_producer_done()
                and consumed >= expected
            ):
                break

            time.sleep(0)

        now = time.perf_counter()

        # Display progress every second.
        if now - last_display >= 1:

            elapsed = (
                now - start_time
            )

            rate = (
                consumed / elapsed
                if elapsed > 0
                else 0
            )

            print(
                f"[Consumer] "
                f"{consumed:,}/{expected:,} "
                f"orders | "
                f"{rate:,.0f} orders/sec | "
                f"Trades: {trades_generated:,}"
            )

            last_display = now

    elapsed = (
        time.perf_counter()
        - start_time
    )

    throughput = (
        consumed / elapsed
        if elapsed > 0
        else 0
    )

    # ========================================================
    # LATENCY CALCULATIONS
    # ========================================================

    latencies_ns.sort()

    if latencies_ns:

        min_latency_ns = (
            latencies_ns[0]
        )

        max_latency_ns = (
            latencies_ns[-1]
        )

        average_latency_ns = (
            sum(latencies_ns)
            / len(latencies_ns)
        )

        p50_ns = percentile(
            latencies_ns,
            50
        )

        p95_ns = percentile(
            latencies_ns,
            95
        )

        p99_ns = percentile(
            latencies_ns,
            99
        )

        p999_ns = percentile(
            latencies_ns,
            99.9
        )

    else:

        min_latency_ns = 0
        max_latency_ns = 0
        average_latency_ns = 0
        p50_ns = 0
        p95_ns = 0
        p99_ns = 0
        p999_ns = 0

    # Convert nanoseconds to microseconds.
    min_latency_us = (
        min_latency_ns / 1_000
    )

    average_latency_us = (
        average_latency_ns / 1_000
    )

    p50_us = p50_ns / 1_000
    p95_us = p95_ns / 1_000
    p99_us = p99_ns / 1_000
    p999_us = p999_ns / 1_000

    max_latency_us = (
        max_latency_ns / 1_000
    )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print()
    print("=" * 65)
    print("Consumer Finished")
    print("=" * 65)

    print(
        f"Orders consumed : {consumed:,}"
    )

    print(
        f"Expected        : {expected:,}"
    )

    print(
        f"Orders missing  : "
        f"{expected - consumed:,}"
    )

    print(
        f"Elapsed time    : "
        f"{elapsed:.6f} sec"
    )

    print(
        f"Throughput      : "
        f"{throughput:,.0f} orders/sec"
    )

    print(
        f"Trades generated: "
        f"{trades_generated:,}"
    )

    print(
        f"Buy orders left : "
        f"{engine.get_buy_order_count():,}"
    )

    print(
        f"Sell orders left: "
        f"{engine.get_sell_order_count():,}"
    )

    print()

    print("-" * 65)
    print("IPC LATENCY")
    print("-" * 65)

    print(
        f"Samples         : "
        f"{len(latencies_ns):,}"
    )

    print(
        f"Minimum         : "
        f"{min_latency_us:.3f} µs"
    )

    print(
        f"Average         : "
        f"{average_latency_us:.3f} µs"
    )

    print(
        f"P50             : "
        f"{p50_us:.3f} µs"
    )

    print(
        f"P95             : "
        f"{p95_us:.3f} µs"
    )

    print(
        f"P99             : "
        f"{p99_us:.3f} µs"
    )

    print(
        f"P99.9           : "
        f"{p999_us:.3f} µs"
    )

    print(
        f"Maximum         : "
        f"{max_latency_us:.3f} µs"
    )

    print("-" * 65)
    print()

    ring_buffer.close()

    # Cleanup IPC file.
    if os.path.exists(IPC_FILE):

        try:
            os.remove(IPC_FILE)

        except PermissionError:

            print(
                "Warning: Could not remove IPC file."
            )


if __name__ == "__main__":
    run_consumer()