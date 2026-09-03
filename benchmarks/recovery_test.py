"""
ChronosMatch Week 4 Resilience / Recovery Test.

Simulates an abrupt producer/process termination after matched trades
have been written to the persistent mmap trade buffer but before they
are flushed to SQLite.

Recovery process:
    1. Create/write trades to trade mmap.
    2. Abruptly terminate the writer with os._exit().
    3. Re-open the existing mmap from a fresh process.
    4. Start TradeFlusher.
    5. Verify every trade reaches SQLite.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from ipc.trade_protocol import Trade
from ipc.trade_ring_buffer import TradeRingBuffer
from persistence.trade_flusher import TradeFlusher
from persistence.trade_ledger import TradeLedger


TRADE_IPC_FILE = "recovery_test.trades.ipc"
DATABASE_FILE = "recovery_test.db"

CAPACITY = 10_000
TRADE_COUNT = 1_000


def cleanup():
    """Remove files from an earlier test run."""

    for filename in (TRADE_IPC_FILE, DATABASE_FILE):
        path = Path(filename)

        if path.exists():
            try:
                path.unlink()
            except PermissionError as error:
                print(
                    f"ERROR: Could not remove {filename}. "
                    "Make sure no previous test process is running."
                )
                raise error


def crash_writer():
    """
    Child process.

    Writes trades to mmap and exits abruptly without closing the
    buffer or flushing anything to SQLite.
    """

    buffer = TradeRingBuffer(
        path=TRADE_IPC_FILE,
        capacity=CAPACITY,
    )

    buffer.create()
    buffer.set_expected_trades(TRADE_COUNT)

    for i in range(TRADE_COUNT):
        trade = Trade(
            trade_id=i + 1,
            buy_order_id=10_000 + i,
            sell_order_id=20_000 + i,
            price=100.0 + (i % 100) * 0.01,
            quantity=(i % 50) + 1,
            timestamp_ns=i + 1,
        )

        while not buffer.write(trade):
            time.sleep(0.0001)

    buffer.mark_producer_done()

    print(
        f"CRASH SIMULATION: wrote {TRADE_COUNT:,} trades "
        "to mmap and exiting abruptly..."
    )

    # Deliberately skip buffer.close().
    os._exit(0)


def run_recovery():
    """Re-open the abandoned mmap and persist all pending trades."""

    print()
    print("=" * 65)
    print("ChronosMatch Week 4 Resilience / Recovery Test")
    print("=" * 65)

    cleanup()

    print()
    print("STEP 1: Starting crash simulation...")

    child_code = (
        "from benchmarks.recovery_test import crash_writer; "
        "crash_writer()"
    )

    result = subprocess.run(
        [sys.executable, "-c", child_code],
        cwd=str(Path.cwd()),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Crash simulation exited with code {result.returncode}"
        )

    if not Path(TRADE_IPC_FILE).exists():
        raise RuntimeError(
            "Recovery failed: trade mmap file was not created."
        )

    print("Crash simulation finished.")
    print("The original writer did not close the mmap.")

    print()
    print("STEP 2: Opening abandoned trade mmap...")

    trade_buffer = TradeRingBuffer(
        path=TRADE_IPC_FILE,
        capacity=CAPACITY,
    )

    trade_buffer.open()

    expected = trade_buffer.get_expected_trades()

    write_pos, read_pos = trade_buffer._get_positions()
    pending = write_pos - read_pos

    print(f"Expected trades : {expected:,}")
    print(f"Trades in mmap  : {pending:,}")

    if pending != TRADE_COUNT:
        trade_buffer.close()
        raise AssertionError(
            f"Expected {TRADE_COUNT} pending trades, "
            f"found {pending}."
        )

    print()
    print("STEP 3: Starting recovery flusher...")

    ledger = TradeLedger(
        database_path=DATABASE_FILE,
    )

    flusher = TradeFlusher(
        trade_buffer=trade_buffer,
        ledger=ledger,
        batch_size=100,
        poll_interval=0.001,
    )

    flusher.start()

    deadline = time.perf_counter() + 10

    while (
        flusher.trades_flushed < TRADE_COUNT
        and flusher.error is None
        and time.perf_counter() < deadline
    ):
        time.sleep(0.01)

    flusher.stop()

    print()
    print("STEP 4: Recovery result")
    print("-" * 65)
    print(f"Trades recovered : {flusher.trades_flushed:,}")
    print(f"Worker error     : {flusher.error}")

    if flusher.error is not None:
        trade_buffer.close()
        ledger.close()
        raise RuntimeError(
            f"Recovery worker failed: {flusher.error}"
        )

    # Open a fresh SQLite connection after the worker has closed its
    # own connection. This also avoids SQLite thread ownership issues.
    verification_ledger = TradeLedger(
        database_path=DATABASE_FILE,
    )
    verification_ledger.open()

    persisted = verification_ledger.count_trades()

    print(f"SQLite persisted : {persisted:,}")

    verification_ledger.close()
    trade_buffer.close()

    print("-" * 65)

    if flusher.trades_flushed != TRADE_COUNT:
        raise AssertionError(
            f"Recovery flushed {flusher.trades_flushed:,} trades; "
            f"expected {TRADE_COUNT:,}."
        )

    if persisted != TRADE_COUNT:
        raise AssertionError(
            f"SQLite contains {persisted:,} trades; "
            f"expected {TRADE_COUNT:,}."
        )

    print()
    print("=" * 65)
    print("RESILIENCE TEST PASSED")
    print("=" * 65)
    print(
        "All trades survived the abrupt process termination "
        "and were recovered into SQLite."
    )
    print("=" * 65)

    cleanup()


if __name__ == "__main__":
    run_recovery()
