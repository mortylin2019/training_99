"""Sequential C beam benchmark — faster for debugging."""
import sys; sys.path.insert(0, 'hijack_tools')
from simulator.c_wrapper import CSimulator
import time

SEEDS = [42, 123, 456, 789, 1024]
DIFFICULTIES = [(0, 'Easy'), (1, 'Normal'), (2, 'Hard'), (3, 'Lunatic')]

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
