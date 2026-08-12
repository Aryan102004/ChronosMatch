"""
ChronosMatch End-to-End IPC Producer.

Generates orders at a controlled rate and writes
them into the mmap ring buffer.
"""

import os
import time

from ipc import RingBuffer, Order, BUY, SELL


IPC_FILE = "e2e_chronosmatch.ipc"

BUFFER_CAPACITY = 100_000

TOTAL_ORDERS = 100_000

# Week 1 controlled benchmark rate.
TARGET_RATE = 100_000


def run_producer():

    # Remove old IPC file.
    if os.path.exists(IPC_FILE):
        os.remove(IPC_FILE)

    ring_buffer = RingBuffer(
        path=IPC_FILE,
        capacity=BUFFER_CAPACITY,
    )

    ring_buffer.create()

    ring_buffer.set_expected_orders(
        TOTAL_ORDERS
    )

    print("=" * 65)
    print("ChronosMatch E2E Producer")
    print("=" * 65)

    print(
        f"Target orders : {TOTAL_ORDERS:,}"
    )

    print(
        f"Target rate   : "
        f"{TARGET_RATE:,} orders/sec"
    )

    print("IPC buffer created.")
    print("Waiting 2 seconds before starting...")
    print()

    # Give the consumer time to connect.
    time.sleep(2)

    start_time = time.perf_counter()

    interval = 1 / TARGET_RATE
    next_send_time = time.perf_counter()

    written = 0
    retries = 0

    for i in range(TOTAL_ORDERS):

        order = Order(
            order_id=i + 1,

            price=(
                245.50
                + (i % 100) * 0.01
            ),

            quantity=(
                (i % 1000) + 1
            ),

            side=(
                BUY
                if i % 2 == 0
                else SELL
            ),

            # RingBuffer.write() sets the timestamp.
            timestamp_ns=0,
        )

        # Write into mmap.
        while not ring_buffer.write(order):

            retries += 1
            time.sleep(0)

        written += 1

        # Maintain target order rate.
        next_send_time += interval

        sleep_time = (
            next_send_time
            - time.perf_counter()
        )

        if sleep_time > 0:
            time.sleep(sleep_time)

    elapsed = (
        time.perf_counter()
        - start_time
    )

    throughput = (
        written / elapsed
        if elapsed > 0
        else 0
    )

    # Tell consumer production is complete.
    ring_buffer.mark_producer_done()

    print()
    print("=" * 65)
    print("Producer Finished")
    print("=" * 65)

    print(
        f"Orders written : {written:,}"
    )

    print(
        f"Buffer retries : {retries:,}"
    )

    print(
        f"Elapsed time   : "
        f"{elapsed:.6f} sec"
    )

    print(
        f"Throughput     : "
        f"{throughput:,.0f} orders/sec"
    )

    print("=" * 65)

    ring_buffer.close()


if __name__ == "__main__":
    run_producer()