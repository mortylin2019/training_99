#!/usr/bin/env python3
"""Profile beam_search speed across DEPTH × WIDTH combinations."""
import sys, os, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from beam_core import beam_search_py, multi_beam_py

N_WARMUP = 50
N_BENCH = 200

def profile(name, fn, px, py, paths, **kw):
    for _ in range(N_WARMUP):
        fn(px, py, paths, **kw)
    t0 = time.perf_counter()
    for _ in range(N_BENCH):
        fn(px, py, paths, **kw)
    dt = (time.perf_counter() - t0) / N_BENCH * 1000
    fps = 1000 / dt if dt > 0 else float('inf')
    print(f"  {name:>30}: {dt:>6.2f}ms ({fps:>6.0f} fps)")
    return dt

np.random.seed(42)
n_bullets = 30  # typical Normal difficulty

print("=== Beam Search Speed Profile ===\n")
print(f"Bullets: {n_bullets} | Warmup: {N_WARMUP} | Bench: {N_BENCH} iterations\n")

# Test various DEPTH × WIDTH
for depth in [40, 80, 120, 160, 200]:
    for width in [6, 8, 12, 20, 35, 50]:
        T = depth + 1
        paths = np.random.uniform(0, 304, (n_bullets, T, 2)).astype(np.float64)
        kw = dict(beam_width=width, beam_depth=depth, check_every=1,
                  danger_base=3000, wall_margin=20,
                  wall_penalty=5000, tw_base=0.5, tw_rate=0.0,
                  early_exit_enabled=True, early_exit_buffer=50000,
                  partial_sort_enabled=True,
                  center_pull_enabled=True, wall_penalty_enabled=True)
        px, py = 152.0, 112.0
        dt = profile(f"D={depth:>3} W={width:>2}", beam_search_py, px, py, paths, **kw)

print("\n=== Multi-Beam (9 parallel) ===\n")

for depth in [40, 80, 120, 160]:
    for width in [6, 8, 12, 20]:
        T = depth + 1
        paths = np.random.uniform(0, 304, (n_bullets, T, 2)).astype(np.float64)
        kw = dict(beam_width=width, beam_depth=depth, check_every=1,
                  danger_base=3000, wall_margin=20,
                  wall_penalty=5000, tw_base=0.5, tw_rate=0.0,
                  early_exit_enabled=True, early_exit_buffer=50000,
                  partial_sort_enabled=True,
                  center_pull_enabled=True, wall_penalty_enabled=True)
        profile(f"MULTI D={depth:>3} W={width:>2}", multi_beam_py, 152.0, 112.0, paths, **kw)

print("\nGame budget: 62 fps = 16ms/frame")
