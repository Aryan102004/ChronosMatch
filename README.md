# ChronosMatch

### Zero-Copy High-Frequency Trading Engine

ChronosMatch is a low-latency trading engine project developed to explore high-frequency trading (HFT) concepts, inter-process communication, memory-mapped data transfer, Cython-based optimization, and real-time order-book matching.

The project is designed around a simple idea:

> **Move high-volume trading data between processes without expensive JSON/Pickle serialization, then execute the performance-critical matching logic using Cython.**

---

## Project Overview

In high-frequency trading, even microseconds can matter.

Traditional Python applications often introduce latency through:

- Python object overhead
- Process-to-process serialization
- JSON/Pickle encoding and decoding
- Interpreter overhead
- Garbage collection and memory management

ChronosMatch addresses the communication bottleneck by using a **memory-mapped ring buffer** to share fixed-size binary order records between processes.

The long-term architecture combines:

- Python
- `mmap`
- `struct`
- `asyncio`
- Cython
- Price-Time Priority matching
- `curses`
- SQLite / ClickHouse

---

# Architecture

The planned ChronosMatch architecture is:

```text
                    Market Simulator
                           │
                           │
                    Python / asyncio
                           │
                           ▼
                ┌────────────────────┐
                │  mmap Ring Buffer  │
                │                    │
                │ Fixed Binary Order │
                │      Records       │
                └─────────┬──────────┘
                          │
                          │ Shared Memory
                          ▼
                ┌────────────────────┐
                │ Cython Matching    │
                │      Engine        │
                │                    │
                │ Limit Order Book   │
                │ Price-Time Priority│
                └─────────┬──────────┘
                          │
              ┌───────────┼────────────┐
              │           │            │
              ▼           ▼            ▼
          Dashboard     Metrics     Trade Ledger
           curses       Latency    SQLite/ClickHouse