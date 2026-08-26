import time

from cython_engine.matching_engine import CythonMatchingEngine


NUM_ORDERS = 100_000


def run_benchmark():

    engine = CythonMatchingEngine()

    trades = 0

    start = time.perf_counter()

    for i in range(NUM_ORDERS):

        is_buy = (i % 2 == 0)

        result = engine.match_order(
            i,
            100.0,
            1,
            is_buy,
            i,
        )

        trades += len(result)

    end = time.perf_counter()

    elapsed = end - start
    throughput = NUM_ORDERS / elapsed

    print()
    print("=" * 60)
    print("ChronosMatch Cython C-Level Throughput Benchmark")
    print("=" * 60)
    print(f"Orders processed : {NUM_ORDERS:,}")
    print(f"Elapsed time     : {elapsed:.6f} sec")
    print(f"Throughput       : {throughput:,.2f} orders/sec")
    print(f"Trades generated : {trades:,}")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()