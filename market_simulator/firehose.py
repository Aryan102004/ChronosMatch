"""
ChronosMatch asynchronous market firehose.

Generates market orders and writes them into
the mmap-based IPC ring buffer.
"""

import asyncio
import os
import time

from ipc import RingBuffer

from .order_generator import OrderGenerator


IPC_FILE = "chronosmatch.ipc"


class MarketFirehose:
    """High-throughput asynchronous market order producer."""

    def __init__(
        self,
        target_rate: int = 1_000,
        buffer_capacity: int = 10_000,
    ):
        self.target_rate = target_rate
        self.buffer_capacity = buffer_capacity

        self.generator = OrderGenerator()

        self.ring_buffer = RingBuffer(
            path=IPC_FILE,
            capacity=buffer_capacity,
        )

        self.orders_generated = 0
        self.orders_written = 0
        self.orders_dropped = 0

        self.start_time = None

    def setup(self):
        """Create the mmap ring buffer."""

        

        self.ring_buffer.create()

    async def start(self, duration: int = 10):
        """Start generating orders."""

        self.start_time = time.perf_counter()

        end_time = (
            self.start_time + duration
        )

        print("=" * 60)
        print("ChronosMatch Market Firehose")
        print("=" * 60)
        print(f"Target rate : {self.target_rate:,} orders/sec")
        print(f"Duration    : {duration} seconds")
        print()

        interval = 1 / self.target_rate

        next_send_time = time.perf_counter()

        while time.perf_counter() < end_time:

            order = self.generator.generate()

            self.orders_generated += 1

            success = self.ring_buffer.write(order)

            if success:
                self.orders_written += 1
            else:
                self.orders_dropped += 1

            next_send_time += interval

            sleep_time = (
                next_send_time
                - time.perf_counter()
            )

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.print_statistics()

    def print_statistics(self):
        """Display firehose statistics."""

        elapsed = (
            time.perf_counter()
            - self.start_time
        )

        actual_rate = (
            self.orders_written / elapsed
            if elapsed > 0
            else 0
        )

        print()
        print("=" * 60)
        print("Firehose Statistics")
        print("=" * 60)

        print(
            f"Elapsed time     : {elapsed:.3f} sec"
        )

        print(
            f"Orders generated : "
            f"{self.orders_generated:,}"
        )

        print(
            f"Orders written   : "
            f"{self.orders_written:,}"
        )

        print(
            f"Orders dropped   : "
            f"{self.orders_dropped:,}"
        )

        print(
            f"Actual rate      : "
            f"{actual_rate:,.2f} orders/sec"
        )

        print("=" * 60)

    def close(self):
        """Close the IPC buffer."""

        self.ring_buffer.close()


async def main():

    firehose = MarketFirehose(
        target_rate=1_000,
    )

    firehose.setup()

    try:
        await firehose.start(
            duration=10,
        )

    finally:
        firehose.close()


if __name__ == "__main__":
    asyncio.run(main())