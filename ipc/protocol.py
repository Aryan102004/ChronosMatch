"""
ChronosMatch IPC binary protocol.

Defines the fixed-size binary representation of a market order.
"""

import struct
from dataclasses import dataclass


# 32-byte fixed-size order record.
#
# Q = unsigned long long -> 8 bytes  (order_id)
# d = double              -> 8 bytes  (price)
# I = unsigned int       -> 4 bytes  (quantity)
# B = unsigned char      -> 1 byte   (side)
# Q = unsigned long long -> 8 bytes  (timestamp)
# 3x = padding            -> 3 bytes
#
# Total = 32 bytes
ORDER_FORMAT = "<QdIBQ3x"

ORDER_SIZE = struct.calcsize(ORDER_FORMAT)


# Order sides
BUY = 1
SELL = 2


@dataclass(slots=True)
class Order:
    """Logical representation of a market order."""

    order_id: int
    price: float
    quantity: int
    side: int
    timestamp_ns: int


def pack_order(order: Order) -> bytes:
    """Convert an Order into its fixed-size binary representation."""

    return struct.pack(
        ORDER_FORMAT,
        order.order_id,
        order.price,
        order.quantity,
        order.side,
        order.timestamp_ns,
    )


def unpack_order(data: bytes) -> Order:
    """Convert binary order data back into an Order."""

    (
        order_id,
        price,
        quantity,
        side,
        timestamp_ns,
    ) = struct.unpack(ORDER_FORMAT, data)

    return Order(
        order_id=order_id,
        price=price,
        quantity=quantity,
        side=side,
        timestamp_ns=timestamp_ns,
    )