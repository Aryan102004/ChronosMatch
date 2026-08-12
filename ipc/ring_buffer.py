"""
ChronosMatch memory-mapped single-producer/single-consumer ring buffer.
"""

import struct
import time
from typing import Optional

from .protocol import (
    ORDER_SIZE,
    Order,
    pack_order,
    unpack_order,
)
from .shared_memory import SharedMemory


CAPACITY = 10_000
HEADER_SIZE = 64
MAGIC = b"CHRO"
VERSION = 1
HEADER_FORMAT = "<4sIQQ"


class RingBuffer:
    """
    Memory-mapped ring buffer.

    Designed initially for a single producer
    and single consumer.
    """

    def __init__(
        self,
        path: str = "chronosmatch.ipc",
        capacity: int = CAPACITY,
    ):
        self.path = path
        self.capacity = capacity

        self.total_size = (
            HEADER_SIZE + (capacity * ORDER_SIZE)
        )

        self.memory = SharedMemory(
            path,
            self.total_size,
        )

        self.mm = None

    def create(self):
        """Create and initialize the ring buffer."""

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

        struct.pack_into("<Q", self.mm, 24, 0)
        struct.pack_into("<B", self.mm, 32, 0)

        self.mm.flush()

    def open(self):
        """Open an existing ring buffer."""

        self.mm = self.memory.open()

        magic, version, _, _ = struct.unpack_from(
            HEADER_FORMAT,
            self.mm,
            0,
        )

        if magic != MAGIC:
            raise RuntimeError(
                "Invalid ChronosMatch IPC buffer."
            )

        if version != VERSION:
            raise RuntimeError(
                f"Unsupported IPC version: {version}"
            )

    def _get_positions(self):
        """Return current write and read positions."""

        _, _, write_pos, read_pos = struct.unpack_from(
            HEADER_FORMAT,
            self.mm,
            0,
        )

        return write_pos, read_pos

    def write(self, order: Order) -> bool:
        """
        Write one order into the ring buffer.

        Timestamp is captured immediately before
        the binary record is written to mmap.
        """

        write_pos, read_pos = self._get_positions()

        if write_pos - read_pos >= self.capacity:
            return False

        # Timestamp as close as practical to the IPC write.
        order.timestamp_ns = time.perf_counter_ns()

        slot = write_pos % self.capacity

        offset = (
            HEADER_SIZE
            + slot * ORDER_SIZE
        )

        data = pack_order(order)

        self.mm[
            offset:offset + ORDER_SIZE
        ] = data

        struct.pack_into(
            "<Q",
            self.mm,
            8,
            write_pos + 1,
        )

        return True

    def read(self) -> Optional[Order]:
        """Read the next order."""

        write_pos, read_pos = self._get_positions()

        if read_pos >= write_pos:
            return None

        slot = read_pos % self.capacity

        offset = (
            HEADER_SIZE
            + slot * ORDER_SIZE
        )

        data = self.mm[
            offset:offset + ORDER_SIZE
        ]

        order = unpack_order(data)

        struct.pack_into(
            "<Q",
            self.mm,
            16,
            read_pos + 1,
        )

        return order

    def is_empty(self) -> bool:
        """Return True if the buffer is empty."""

        write_pos, read_pos = self._get_positions()
        return write_pos == read_pos

    def is_full(self) -> bool:
        """Return True if the buffer is full."""

        write_pos, read_pos = self._get_positions()

        return (
            write_pos - read_pos
            >= self.capacity
        )

    def set_expected_orders(self, count: int):
        """Store the number of orders the producer intends to write."""

        struct.pack_into(
            "<Q",
            self.mm,
            24,
            count,
        )

    def get_expected_orders(self) -> int:
        """Return the expected number of orders."""

        return struct.unpack_from(
            "<Q",
            self.mm,
            24,
        )[0]

    def mark_producer_done(self):
        """Tell the consumer that the producer has finished."""

        struct.pack_into(
            "<B",
            self.mm,
            32,
            1,
        )

    def is_producer_done(self) -> bool:
        """Check whether the producer has finished."""

        return (
            struct.unpack_from(
                "<B",
                self.mm,
                32,
            )[0] == 1
        )

    def close(self):
        """Close the ring buffer."""

        self.memory.close()
        self.mm = None