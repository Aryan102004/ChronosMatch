"""
ChronosMatch Whale-Order Terminal Demo.

Creates several resting SELL price levels and then sends one large
BUY order that consumes multiple levels. The consumer's Whale alert
logic can be demonstrated independently through analyze_whale_order().
"""

from dataclasses import dataclass

from consumer.consumer import (
    WHALE_QUANTITY_THRESHOLD,
    analyze_whale_order,
)


@dataclass
class DemoOrder:
    order_id: int
    price: float
    quantity: int
    side: int


def run_demo():
    """Run a deterministic terminal-only Whale detection demonstration."""

    # These trade records mirror the dictionaries returned by the
    # Cython matching engine.
    whale_order = DemoOrder(
        order_id=9001,
        price=105.00,
        quantity=10_000,
        side=1,
    )

    trades = [
        {
            "buy_order_id": 9001,
            "sell_order_id": 1001,
            "price": 100.00,
            "quantity": 3_000,
        },
        {
            "buy_order_id": 9001,
            "sell_order_id": 1002,
            "price": 100.50,
            "quantity": 3_000,
        },
        {
            "buy_order_id": 9001,
            "sell_order_id": 1003,
            "price": 101.00,
            "quantity": 4_000,
        },
    ]

    is_whale, levels, matched_quantity = analyze_whale_order(
        whale_order,
        trades,
    )

    print("=" * 72)
    print("                 CHRONOSMATCH WHALE DEMO")
    print("=" * 72)
    print(
        f"Whale threshold   : "
        f"{WHALE_QUANTITY_THRESHOLD:,} quantity"
    )
    print(
        f"Order quantity    : "
        f"{whale_order.quantity:,}"
    )
    print(
        f"Levels cleared    : "
        f"{levels}"
    )
    print(
        f"Matched quantity  : "
        f"{matched_quantity:,}"
    )
    print(
        f"Whale detected    : "
        f"{'YES' if is_whale else 'NO'}"
    )
    print("=" * 72)

    if not is_whale:
        raise AssertionError(
            "Whale demo failed: multi-level large order was "
            "not detected."
        )

    print()
    print("WHALE UI LOGIC PASSED")


if __name__ == "__main__":
    run_demo()
