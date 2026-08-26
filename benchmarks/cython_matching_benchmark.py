import time

from cython_engine.matching_engine import CythonMatchingEngine


NUM_ORDERS = 100_000


def run_benchmark():
    engine = CythonMatchingEngine()

    start = time.perf_counter()

    trades = 0

    for i in range(NUM_ORDERS):
        # Alternate BUY/SELL orders so the engine
        # exercises the matching path.
        is_buy = (i % 2 == 0)

        result = engine.match_order(
            i,
            100.0,
            1,
            is_buy,
            i,
        )

        trades += len(result)

    elapsed = time.perf_counter() - start

    throughput = NUM_ORDERS / elapsed

    print()
    print("=" * 60)
    print("ChronosMatch Cython Matching Benchmark")
    print("=" * 60)
    print(f"Orders processed : {NUM_ORDERS:,}")
    print(f"Elapsed time     : {elapsed:.6f} sec")
    print(f"Throughput       : {throughput:,.2f} orders/sec")
    print(f"Trades generated : {trades:,}")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()