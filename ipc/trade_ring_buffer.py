"""
ChronosMatch memory-mapped single-producer/single-consumer
ring buffer for matched trades.
"""

import struct
from typing import Optional

from .trade_protocol import (
    TRADE_SIZE,
    Trade,
    pack_trade,
    unpack_trade,
)
from .shared_memory import SharedMemory


CAPACITY = 10_000

# Keep the same 64-byte header design as the order ring buffer.
HEADER_SIZE = 64

MAGIC = b"TRDE"
VERSION = 1

# Header:
# 0  - 4 bytes  : magic
# 4  - 4 bytes  : version
# 8  - 8 bytes  : write position
# 16 - 8 bytes  : read position
HEADER_FORMAT = "<4sIQQ"


class TradeRingBuffer:
    """
    Memory-mapped ring buffer for matched trades.

    Designed for a single producer and a single consumer.

    Producer:
        ChronosMatch consumer / matching pipeline

    Consumer:
        Background trade flusher
    """

    def __init__(
        self,
        path: str = "chronosmatch.trades.ipc",
        capacity: int = CAPACITY,
    ):
        self.path = path
        self.capacity = capacity

        self.total_size = (
            HEADER_SIZE + (capacity * TRADE_SIZE)
        )

        self.memory = SharedMemory(
            path,
            self.total_size,
        )

        self.mm = None

    def create(self):
        """Create and initialize the trade ring buffer."""

        self.mm = self.memory.create()

        struct.pack_into(
            HEADER_FORMAT,
            self.mm,
            0,
            MAGIC,
            VERSION,
            0,
            0,
        )

        # Expected trade count.
        struct.pack_into(
            "<Q",
            self.mm,
            24,
            0,
        )

        # Producer-done flag.
        struct.pack_into(
            "<B",
            self.mm,
            32,
            0,
        )

        self.mm.flush()

    def open(self):
        """Open an existing trade ring buffer."""

        self.mm = self.memory.open()

        magic, version, _, _ = struct.unpack_from(
            HEADER_FORMAT,
            self.mm,
            0,
        )

        if magic != MAGIC:
            raise RuntimeError(
                "Invalid ChronosMatch trade IPC buffer."
            )

        if version != VERSION:
            raise RuntimeError(
                f"Unsupported trade IPC version: {version}"
            )

    def _get_positions(self):
        """Return current write and read positions."""

        _, _, write_pos, read_pos = struct.unpack_from(
            HEADER_FORMAT,
            self.mm,
            0,
        )

        return write_pos, read_pos

    def write(self, trade: Trade) -> bool:
        """
        Write one trade into the ring buffer.

        Returns:
            True  - trade written successfully
            False - buffer is full
        """

        write_pos, read_pos = self._get_positions()

        if write_pos - read_pos >= self.capacity:
            return False

        slot = write_pos % self.capacity

        offset = (
            HEADER_SIZE
            + slot * TRADE_SIZE
        )

        data = pack_trade(trade)

        self.mm[
            offset:offset + TRADE_SIZE
        ] = data

        # Publish the new write position only after
        # the complete trade record has been written.
        struct.pack_into(
            "<Q",
            self.mm,
            8,
            write_pos + 1,
        )

        return True

    def read(self) -> Optional[Trade]:
        """
        Read the next trade from the ring buffer.

        Returns:
            Trade object if available.
            None if the buffer is empty.
        """

        write_pos, read_pos = self._get_positions()

        if read_pos >= write_pos:
            return None

        slot = read_pos % self.capacity

        offset = (
            HEADER_SIZE
            + slot * TRADE_SIZE
        )

        data = self.mm[
            offset:offset + TRADE_SIZE
        ]

        trade = unpack_trade(data)

        # Publish the new read position after the
        # complete trade record has been read.
        struct.pack_into(
            "<Q",
            self.mm,
            16,
            read_pos + 1,
        )

        return trade

    def is_empty(self) -> bool:
        """Return True if the trade buffer is empty."""

        write_pos, read_pos = self._get_positions()

        return write_pos == read_pos

    def is_full(self) -> bool:
        """Return True if the trade buffer is full."""

        write_pos, read_pos = self._get_positions()

        return (
            write_pos - read_pos
            >= self.capacity
        )

    def set_expected_trades(self, count: int):
        """Store the number of trades expected."""

        struct.pack_into(
            "<Q",
            self.mm,
            24,
            count,
        )

    def get_expected_trades(self) -> int:
        """Return the expected number of trades."""

        return struct.unpack_from(
            "<Q",
            self.mm,
            24,
        )[0]

    def mark_producer_done(self):
        """Tell the trade consumer that production is finished."""

        struct.pack_into(
            "<B",
            self.mm,
            32,
            1,
        )

    def is_producer_done(self) -> bool:
        """Check whether the trade producer has finished."""

        return (
            struct.unpack_from(
                "<B",
                self.mm,
                32,
            )[0] == 1
        )

    def close(self):
        """Close the trade ring buffer."""

        self.memory.close()
        self.mm = None