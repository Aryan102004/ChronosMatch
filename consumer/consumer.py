"""
ChronosMatch IPC Consumer.

Reads orders from the mmap ring buffer and sends them
to the Cython matching engine.
"""

import os
import time

from ipc import RingBuffer, BUY, SELL
from cython_engine.matching_engine import CythonMatchingEngine


IPC_FILE = "chronosmatch.ipc"
BUFFER_CAPACITY = 10_000


class OrderConsumer:
    """Consumes orders from the shared mmap ring buffer."""

    def __init__(
        self,
        ipc_file: str = IPC_FILE,
        buffer_capacity: int = BUFFER_CAPACITY,
    ):
        self.ipc_file = ipc_file
        self.buffer_capacity = buffer_capacity

        self.ring_buffer = RingBuffer(
            path=self.ipc_file,
            capacity=self.buffer_capacity,
        )

        self.engine = CythonMatchingEngine()

        self.orders_consumed = 0
        self.trades_generated = 0
        self.start_time = None

    def connect(self):
        """Open the existing mmap ring buffer."""

        if not os.path.exists(self.ipc_file):
            raise FileNotFoundError(
                f"IPC file not found: {self.ipc_file}\n"
                "Start the market firehose first."
            )

        self.ring_buffer.open()

        print("Connected to ChronosMatch IPC.")
        print("Cython matching engine initialized.")
        print("Waiting for orders...\n")

    def process_order(self, order):
        """Send one IPC order to the Cython matching engine."""

        is_buy = order.side == BUY

        trades = self.engine.match_order(
            order.order_id,
            order.price,
            order.quantity,
            is_buy,
            order.timestamp_ns,
        )

        self.orders_consumed += 1
        self.trades_generated += len(trades)

        return trades

    def consume(self, duration: int = 10):
        """Consume and process orders for the specified duration."""

        self.start_time = time.perf_counter()

        end_time = self.start_time + duration
        last_display = self.start_time

        while time.perf_counter() < end_time:

            order = self.ring_buffer.read()

            if order is None:
                time.sleep(0.0001)
                continue

            trades = self.process_order(order)

            if self.orders_consumed <= 10:

                side = (
                    "BUY"
                    if order.side == BUY
                    else "SELL"
                )

                print(
                    f"Order ID={order.order_id:<6} "
                    f"Side={side:<4} "
                    f"Price={order.price:>8.2f} "
                    f"Qty={order.quantity:<5} "
                    f"Trades={len(trades)}"
                )

            current_time = time.perf_counter()

            if current_time - last_display >= 1:

                self.display_statistics(
                    current_time
                )

                last_display = current_time

    def display_statistics(self, current_time):
        """Display current consumer statistics."""

        elapsed = current_time - self.start_time

        rate = (
            self.orders_consumed / elapsed
            if elapsed > 0
            else 0
        )

        print(
            f"\n[Consumer] "
            f"Orders: {self.orders_consumed:,} | "
            f"Rate: {rate:,.0f} orders/sec | "
            f"Trades: {self.trades_generated:,}"
        )

    def print_final_statistics(self):
        """Display final consumer statistics."""

        elapsed = (
            time.perf_counter()
            - self.start_time
        )

        rate = (
            self.orders_consumed / elapsed
            if elapsed > 0
            else 0
        )

        print("\n")
        print("=" * 60)
        print("ChronosMatch Consumer Statistics")
        print("=" * 60)

        print(
            f"Elapsed time     : {elapsed:.3f} sec"
        )

        print(
            f"Orders consumed  : "
            f"{self.orders_consumed:,}"
        )

        print(
            f"Average rate     : "
            f"{rate:,.2f} orders/sec"
        )

        print(
            f"Trades generated : "
            f"{self.trades_generated:,}"
        )

        print(
            f"Buy orders       : "
            f"{self.engine.get_buy_order_count():,}"
        )

        print(
            f"Sell orders      : "
            f"{self.engine.get_sell_order_count():,}"
        )

        print("=" * 60)

    def close(self):
        """Close the mmap buffer."""

        self.ring_buffer.close()


def main():

    consumer = OrderConsumer()

    try:

        consumer.connect()

        consumer.consume(duration=10)

        consumer.print_final_statistics()

    except KeyboardInterrupt:

        print("\nConsumer stopped by user.")

    except FileNotFoundError as error:

        print(f"\nERROR: {error}")

    finally:

        consumer.close()


if __name__ == "__main__":
    main()