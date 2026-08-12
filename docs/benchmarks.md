# ChronosMatch Week 1 Benchmarks

## IPC Baseline

The initial ChronosMatch IPC implementation uses:

- Python `mmap`
- Python `struct`
- Fixed 32-byte order records
- Single-producer / single-consumer ring buffer
- Separate producer and consumer processes

### Test Configuration

- Total orders: 100,000
- Target rate: 1,000 orders/sec
- Orders lost: 0

### Results

| Metric | Result |
|---|---:|
| Orders written | 100,000 |
| Orders consumed | 100,000 |
| Orders missing | 0 |
| Producer throughput | 1,000 orders/sec |
| Consumer throughput | 981 orders/sec |
| Average IPC latency | 11.425 µs |
| P50 latency | 7.600 µs |
| P95 latency | 21.600 µs |
| P99 latency | 45.800 µs |
| P99.9 latency | 498.300 µs |
| Maximum latency | 7,519.800 µs |

### Interpretation

The mmap-based IPC successfully transferred all 100,000 orders without data loss.

At a controlled rate of 1,000 orders/sec, the median producer-to-consumer IPC latency was 7.6 µs and the P99 latency was 45.8 µs.

The higher P99.9 and maximum values indicate occasional tail-latency spikes, which are expected in a Python process running on a general-purpose operating system.

These measurements represent IPC latency only and should not be interpreted as matching-engine latency.