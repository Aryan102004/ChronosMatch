"""
ChronosMatch asynchronous trade persistence.

Reads matched trades from the mmap trade ring buffer
and asynchronously flushes them to the SQLite ledger.
"""

import threading
import time

from ipc.trade_ring_buffer import TradeRingBuffer
from persistence.trade_ledger import TradeLedger


class TradeFlusher:
    """
    Background worker that moves trades from the mmap
    trade buffer into the persistent SQLite ledger.

    The SQLite connection belongs exclusively to the
    background worker thread.
    """

    def __init__(
        self,
        trade_buffer: TradeRingBuffer,
        ledger: TradeLedger,
        batch_size: int = 100,
        poll_interval: float = 0.001,
    ):
        self.trade_buffer = trade_buffer
        self.ledger = ledger

        self.batch_size = batch_size
        self.poll_interval = poll_interval

        self._stop_event = threading.Event()
        self._thread = None

        self.trades_flushed = 0
        self.error = None

    def start(self):
        """Start the background flushing thread."""

        if self._thread is not None:
            raise RuntimeError(
                "Trade flusher is already running."
            )

        self._stop_event.clear()
        self.error = None
        self.trades_flushed = 0

        self._thread = threading.Thread(
            target=self._run,
            name="ChronosMatch-TradeFlusher",
            daemon=True,
        )

        self._thread.start()

    def _run(self):
        """
        Background worker loop.

        The SQLite connection is opened inside this thread
        and is therefore owned exclusively by this thread.
        """

        try:
            # ----------------------------------------------------
            # SQLite connection belongs to this worker thread.
            # ----------------------------------------------------

            self.ledger.open()

            while not self._stop_event.is_set():

                trades = self._read_batch()

                if trades:

                    self.ledger.insert_trades(
                        trades
                    )

                    self.ledger.commit()

                    self.trades_flushed += len(
                        trades
                    )

                else:

                    time.sleep(
                        self.poll_interval
                    )

            # ----------------------------------------------------
            # FINAL DRAIN
            #
            # When stop() is called, there may still be trades
            # waiting inside the mmap buffer.
            # ----------------------------------------------------

            self._flush_remaining()

        except Exception as error:

            self.error = error

        finally:

            # ----------------------------------------------------
            # IMPORTANT:
            #
            # The SQLite connection must be closed by the SAME
            # thread that created it.
            # ----------------------------------------------------

            try:
                self.ledger.close()

            except Exception as close_error:

                if self.error is None:
                    self.error = close_error

    def _read_batch(self):
        """Read up to batch_size trades from the mmap buffer."""

        trades = []

        for _ in range(self.batch_size):

            trade = self.trade_buffer.read()

            if trade is None:
                break

            trades.append(trade)

        return trades

    def _flush_remaining(self):
        """
        Persist all trades remaining in the mmap buffer.

        Continues until the trade buffer is empty.
        """

        while True:

            trades = self._read_batch()

            if not trades:
                break

            self.ledger.insert_trades(
                trades
            )

            self.ledger.commit()

            self.trades_flushed += len(
                trades
            )

    def stop(self):
        """
        Stop the background worker.

        The worker performs a final drain and closes
        the SQLite connection before this method returns.
        """

        if self._thread is None:
            return

        self._stop_event.set()

        self._thread.join()

        self._thread = None

    def is_running(self) -> bool:
        """Return True if the background worker is running."""

        return (
            self._thread is not None
            and self._thread.is_alive()
        )