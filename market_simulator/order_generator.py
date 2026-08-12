"""
ChronosMatch Market Order Generator.

Generates realistic mock BUY and SELL orders
for the market firehose.
"""

import random
import time

from ipc import Order, BUY, SELL


class OrderGenerator:
    """Generate mock market orders."""

    def __init__(
        self,
        starting_price: float = 245.50,
        price_range: float = 2.00,
        min_quantity: int = 1,
        max_quantity: int = 1000,
    ):
        self.current_price = starting_price
        self.price_range = price_range

        self.min_quantity = min_quantity
        self.max_quantity = max_quantity

        self.order_id = 0

    def generate(self) -> Order:
        """Generate one market order."""

        self.order_id += 1

        # Random BUY / SELL
        side = random.choice([BUY, SELL])

        # Generate price around current market price
        price = round(
            self.current_price
            + random.uniform(
                -self.price_range,
                self.price_range,
            ),
            2,
        )

        # Generate random quantity
        quantity = random.randint(
            self.min_quantity,
            self.max_quantity,
        )

        # Nanosecond timestamp
        timestamp_ns = time.perf_counter_ns()

        return Order(
            order_id=self.order_id,
            price=price,
            quantity=quantity,
            side=side,
            timestamp_ns=timestamp_ns,
        )