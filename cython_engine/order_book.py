from dataclasses import dataclass
from typing import Literal


@dataclass
class Order:
    order_id: int
    price: float
    quantity: int
    side: Literal["BUY", "SELL"]
    timestamp: int


class OrderBook:

    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []
        self.orders = {}

    def add_order(self, order: Order):
        self.orders[order.order_id] = order

        if order.side == "BUY":
            self.buy_orders.append(order)
        else:
            self.sell_orders.append(order)

    def cancel_order(self, order_id: int):
        order = self.orders.get(order_id)

        if order is None:
            return False

        if order.side == "BUY":
            self.buy_orders.remove(order)
        else:
            self.sell_orders.remove(order)

        del self.orders[order_id]

        return True

    def match_order(self, incoming_order: Order):
        trades = []

        if incoming_order.side == "BUY":

            opposite_orders = sorted(
                self.sell_orders,
                key=lambda x: (x.price, x.timestamp)
            )

            for resting_order in opposite_orders:

                if incoming_order.price < resting_order.price:
                    break

                trade_quantity = min(
                    incoming_order.quantity,
                    resting_order.quantity
                )

                trades.append({
                    "buy_order_id": incoming_order.order_id,
                    "sell_order_id": resting_order.order_id,
                    "price": resting_order.price,
                    "quantity": trade_quantity
                })

                incoming_order.quantity -= trade_quantity
                resting_order.quantity -= trade_quantity

                if resting_order.quantity == 0:
                    self.sell_orders.remove(resting_order)
                    del self.orders[resting_order.order_id]

                if incoming_order.quantity == 0:
                    break

            if incoming_order.quantity > 0:
                self.add_order(incoming_order)

        else:

            opposite_orders = sorted(
                self.buy_orders,
                key=lambda x: (-x.price, x.timestamp)
            )

            for resting_order in opposite_orders:

                if incoming_order.price > resting_order.price:
                    break

                trade_quantity = min(
                    incoming_order.quantity,
                    resting_order.quantity
                )

                trades.append({
                    "buy_order_id": resting_order.order_id,
                    "sell_order_id": incoming_order.order_id,
                    "price": resting_order.price,
                    "quantity": trade_quantity
                })

                incoming_order.quantity -= trade_quantity
                resting_order.quantity -= trade_quantity

                if resting_order.quantity == 0:
                    self.buy_orders.remove(resting_order)
                    del self.orders[resting_order.order_id]

                if incoming_order.quantity == 0:
                    break

            if incoming_order.quantity > 0:
                self.add_order(incoming_order)

        return trades

    def display(self):
        print("\n========== ORDER BOOK ==========")

        print("\nSELL ORDERS")

        for order in sorted(
            self.sell_orders,
            key=lambda x: (x.price, x.timestamp)
        ):
            print(
                f"ID={order.order_id} "
                f"Price={order.price:.2f} "
                f"Qty={order.quantity}"
            )

        print("\nBUY ORDERS")

        for order in sorted(
            self.buy_orders,
            key=lambda x: (-x.price, x.timestamp)
        ):
            print(
                f"ID={order.order_id} "
                f"Price={order.price:.2f} "
                f"Qty={order.quantity}"
            )

        print("===============================\n")