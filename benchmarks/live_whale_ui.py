"""Deterministic live Whale UI demonstration.

Uses the production whale-analysis and terminal-alert functions from
consumer.consumer without starting the real IPC/SQLite consumer.
"""

from dataclasses import dataclass

from ipc import BUY
from consumer.consumer import (
    WHALE_QUANTITY_THRESHOLD,
    OrderConsumer,
    analyze_whale_order,
)


@dataclass
class DemoOrder:
    order_id: int
    price: float
    quantity: int
    side: int


def main():
    order = DemoOrder(
        order_id=9001,
        price=105.00,
        quantity=10_000,
        side=BUY,
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

    is_whale, levels_cleared, matched_quantity = analyze_whale_order(
        order, trades
    )

    print("=" * 65)
    print("              CHRONOSMATCH LIVE WHALE UI")
    print("=" * 65)
    print(f"Whale threshold     : {WHALE_QUANTITY_THRESHOLD:,}")
    print(f"Order quantity      : {order.quantity:,}")
    print(f"Levels cleared      : {levels_cleared}")
    print(f"Matched quantity    : {matched_quantity:,}")
    print(f"Whale detected      : {'YES' if is_whale else 'NO'}")

    if is_whale:
        # Call the exact production terminal UI method.
        OrderConsumer.display_whale_alert(
            None,
            order,
            levels_cleared,
            matched_quantity,
        )

    assert is_whale
    assert levels_cleared == 3
    assert matched_quantity == 10_000

    print("LIVE WHALE UI DEMO PASSED")


if __name__ == "__main__":
    main()
