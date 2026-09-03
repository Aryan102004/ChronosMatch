"""
ChronosMatch binary protocol for matched trades.

Defines the fixed-size binary representation of a trade
written to the trade mmap ring buffer.
"""

import struct
from dataclasses import dataclass


# Fixed-size trade record.
#
# Q = unsigned long long -> 8 bytes  (trade_id)
# Q = unsigned long long -> 8 bytes  (buy_order_id)
# Q = unsigned long long -> 8 bytes  (sell_order_id)
# d = double             -> 8 bytes  (price)
# I = unsigned int       -> 4 bytes  (quantity)
# Q = unsigned long long -> 8 bytes  (timestamp_ns)
#
# Total = 44 bytes
#
# Using '<' gives little-endian layout with standard sizes
# and no automatic alignment padding.
TRADE_FORMAT = "<QQQdIQ"

TRADE_SIZE = struct.calcsize(TRADE_FORMAT)


@dataclass(slots=True)
class Trade:
    """Logical representation of a matched trade."""

    trade_id: int
    buy_order_id: int
    sell_order_id: int
    price: float
    quantity: int
    timestamp_ns: int


def pack_trade(trade: Trade) -> bytes:
    """Convert a Trade into its fixed-size binary representation."""

    return struct.pack(
        TRADE_FORMAT,
        trade.trade_id,
        trade.buy_order_id,
        trade.sell_order_id,
        trade.price,
        trade.quantity,
        trade.timestamp_ns,
    )


def unpack_trade(data: bytes) -> Trade:
    """Convert binary trade data back into a Trade."""

    (
        trade_id,
        buy_order_id,
        sell_order_id,
        price,
        quantity,
        timestamp_ns,
    ) = struct.unpack(TRADE_FORMAT, data)

    return Trade(
        trade_id=trade_id,
        buy_order_id=buy_order_id,
        sell_order_id=sell_order_id,
        price=price,
        quantity=quantity,
        timestamp_ns=timestamp_ns,
    )