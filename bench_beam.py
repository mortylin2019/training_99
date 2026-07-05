"""
bench_beam.py — C beam search benchmark across all difficulties.
Parallel (8 workers) or sequential mode.
Usage: python bench_beam.py [--sequential]
"""
import sys, os
_dir = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_dir)
if _parent not in sys.path:
    sys.path.insert(0, _parent)
from hijack_tools.bench_worker import test_seed
from concurrent.futures import ProcessPoolExecutor
import time

SEEDS = [42, 123, 456, 789, 1024, 2048, 4096, 7777, 9999, 1337]
DIFFICULTIES = [(0, 'Easy'), (1, 'Normal'), (2, 'Hard'), (3, 'Lunatic')]


def run_parallel():
    print("=" * 60)
    print("  C Beam Search — Parallel Benchmark (8 workers)")
    print(f"  Seeds: {len(SEEDS)} per difficulty, 100s cap")
    print("=" * 60)

    for diff, name in DIFFICULTIES:
        t0 = time.perf_counter()
        args = [(diff, s) for s in SEEDS]
        with ProcessPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(test_seed, args))
        survivals = [r[2] for r in results]
        caps = sum(1 for s in survivals if s >= 99.0)
        avg = sum(survivals) / len(survivals)
        dt = time.perf_counter() - t0

        print(f"\n{'─' * 50}")
        print(f"  Diff {diff} ({name:7s}): {len(SEEDS)} seeds")
        print(f"  Avg: {avg:5.1f}s  |  Caps: {caps}/{len(SEEDS)}")
        print(f"  Best: {max(survivals):5.1f}s  Worst: {min(survivals):5.1f}s")
        print(f"  Wall: {dt:.1f}s ({dt / len(SEEDS):.1f}s/seed)")
        print(f"  Times: {[f'{s:.0f}s' for s in survivals]}")
        print(f"{'─' * 50}")

    print(f"\n{'=' * 60}\n  Done.\n{'=' * 60}")


def run_sequential():
    """Fallback: sequential mode (simpler, works always)."""
    import sys; sys.path.insert(0, 'hijack_tools')
    from simulator.c_wrapper import CSimulator

    print("=" * 60)
    print("  C Beam Search — Sequential Benchmark")
    print(f"  Seeds: {len(SEEDS)} per difficulty, 100s cap")
    print("=" * 60)

    for diff, name in DIFFICULTIES:
        t0 = time.perf_counter()
        surv = []; caps = 0
        for s in SEEDS:
            cs = CSimulator(diff, s)
            for _ in range(50): cs.step(0)
            for f in range(8000):
                if not cs.step(cs.beam_search()):
                    surv.append(f / 80.0); break
            else:
                surv.append(100.0); caps += 1
        dt = time.perf_counter() - t0
        avg = sum(surv) / len(surv)
        print(f"  {name:7s}: avg={avg:5.1f}s  caps={caps}/{len(SEEDS)}  "
              f"best={max(surv):.0f}s  worst={min(surv):.0f}s  wall={dt:.0f}s  "
              f"times={[f'{x:.0f}s' for x in surv]}")

    print("=" * 60 + "\nDone.")


if __name__ == '__main__':
    import sys
    if '--sequential' in sys.argv:
        run_sequential()
    else:
        run_parallel()
