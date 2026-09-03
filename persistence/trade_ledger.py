"""
ChronosMatch persistent trade ledger.

Stores matched trades in SQLite for durable auditing.
"""

import sqlite3
from pathlib import Path

from ipc.trade_protocol import Trade


DEFAULT_DATABASE = "chronosmatch.db"


class TradeLedger:
    """
    Persistent SQLite ledger for matched trades.

    Database writes are intentionally kept outside the
    matching engine hot path.
    """

    def __init__(
        self,
        database_path: str = DEFAULT_DATABASE,
    ):
        self.database_path = Path(database_path)
        self.connection = None

    def open(self):
        """Open the SQLite database and initialize the ledger."""

        self.connection = sqlite3.connect(
            self.database_path
        )

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY,
                buy_order_id INTEGER NOT NULL,
                sell_order_id INTEGER NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL
            )
            """
        )

        self.connection.commit()

    def insert_trade(self, trade: Trade):
        """Insert one trade into the ledger."""

        if self.connection is None:
            raise RuntimeError(
                "Trade ledger has not been opened."
            )

        self.connection.execute(
            """
            INSERT OR IGNORE INTO trades (
                trade_id,
                buy_order_id,
                sell_order_id,
                price,
                quantity,
                timestamp_ns
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                trade.trade_id,
                trade.buy_order_id,
                trade.sell_order_id,
                trade.price,
                trade.quantity,
                trade.timestamp_ns,
            ),
        )

    def insert_trades(self, trades):
        """
        Insert multiple trades in one SQLite transaction.

        Batch insertion is significantly preferable to
        committing every individual trade.
        """

        if self.connection is None:
            raise RuntimeError(
                "Trade ledger has not been opened."
            )

        self.connection.executemany(
            """
            INSERT OR IGNORE INTO trades (
                trade_id,
                buy_order_id,
                sell_order_id,
                price,
                quantity,
                timestamp_ns
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    trade.trade_id,
                    trade.buy_order_id,
                    trade.sell_order_id,
                    trade.price,
                    trade.quantity,
                    trade.timestamp_ns,
                )
                for trade in trades
            ],
        )

    def commit(self):
        """Commit pending transactions."""

        if self.connection is None:
            raise RuntimeError(
                "Trade ledger has not been opened."
            )

        self.connection.commit()

    def count_trades(self) -> int:
        """Return the number of persisted trades."""

        if self.connection is None:
            raise RuntimeError(
                "Trade ledger has not been opened."
            )

        cursor = self.connection.execute(
            "SELECT COUNT(*) FROM trades"
        )

        return cursor.fetchone()[0]

    def close(self):
        """Commit pending work and close the database."""

        if self.connection is not None:
            self.connection.commit()
            self.connection.close()
            self.connection = None