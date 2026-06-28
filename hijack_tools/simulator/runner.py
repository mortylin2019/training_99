"""
simulator/runner.py - AI test harness with ProcessPool + tqdm.

Usage: python -m hijack_tools.simulator.runner --ai ai_beam --runs 500
"""
import math
import time
import os
from concurrent.futures import ProcessPoolExecutor

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from .engine import GameSimulator
from .bullet import Bullet
from .config import FPS


def _load_ai(name):
    if name == "ai_beam":
        try: from ai_beam import BeamAI
        except ImportError: from hijack_tools.ai_beam import BeamAI
        return BeamAI
    if name == "ai_direct":
        try: from ai_direct import SuperiorAI
        except ImportError: from hijack_tools.ai_direct import SuperiorAI
        return SuperiorAI
    if name == "ai_rl":
        try: from ai_rl import RLAgent
        except ImportError: from hijack_tools.ai_rl import RLAgent
        return RLAgent
    raise ValueError(f"Unknown AI: {name}")


def _run_one(args):
    """Single simulation (picklable for ProcessPool)."""
    ai_name, difficulty, max_frames, seed, spawn_interval_ms = args
    from .tables import VEL_TABLE, ACCEL_TABLE

    AI = _load_ai(ai_name)
    ai = AI(vel_table=VEL_TABLE, accel_table=ACCEL_TABLE)
    sim = GameSimulator(difficulty=difficulty, seed=seed,
                        spawn_interval_ms=spawn_interval_ms)

    # Warmup AI
    fake = [Bullet(raw_x=0x8000, raw_y=0x4000, angle_index=i) for i in range(20)]
    for _ in range(3):
        ai.decide(152, 44, fake)

    for _ in range(max_frames):
        bits = ai.decide(sim.px, sim.py, sim.get_visible_bullets())
        alive, _ = sim.step(bits)
        if not alive:
            return sim.frame
    return max_frames


def run_benchmark(ai_name="ai_beam", runs=100, difficulty=1, max_frames=30000,
                  workers=0, spawn_interval_ms=None):
    """Run benchmark and return results dict."""
    workers = workers or os.cpu_count() or 4
    tasks = [(ai_name, difficulty, max_frames, i * 12345, spawn_interval_ms)
             for i in range(runs)]
    results = []
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=workers) as pool:
        iterator = pool.map(_run_one, tasks)
        if HAS_TQDM:
            for f in tqdm(iterator, total=runs, desc="Simulating", unit="run"):
                results.append(f)
        else:
            for i, f in enumerate(iterator):
                results.append(f)
                if (i + 1) % max(1, runs // 10) == 0:
                    print(f"  {i+1}/{runs}")

    elapsed = time.time() - t0
    times = [f / FPS for f in results]
    st = sorted(times)
    n = len(st)

    return {
        "ai": ai_name, "runs": n, "elapsed": elapsed,
        "best": max(times), "worst": min(times),
        "avg": sum(times) / n, "median": st[n // 2],
        "p90": st[int(n * .9)], "p75": st[int(n * .75)],
        "p25": st[int(n * .25)],
        "times": times, "frames": results,
    }


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--ai", default="ai_beam")
    p.add_argument("--runs", type=int, default=200)
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=int(100 * FPS),
                   help=f"Max frames ({100*FPS}={100*FPS//FPS}s at {FPS}fps)")
    p.add_argument("--spawn-interval", type=int, default=None,
                   help="Override spawn interval in ms (default 3000)")
    p.add_argument("-j", "--workers", type=int, default=0)
    args = p.parse_args()

    print(f"Simulator: {args.runs} runs, {args.ai}, diff {args.difficulty}")
    r = run_benchmark(args.ai, args.runs, args.difficulty, args.max_frames,
                      args.workers, args.spawn_interval)

    print(f"\n{'='*60}")
    print(f"  {r['runs']} runs in {r['elapsed']:.0f}s "
          f"({r['runs']/r['elapsed']:.0f} run/s)")
    max_t = r["best"]
    cap_hit = sum(1 for t in r["times"] if t >= max_t * 0.99)
    print(f"  Cap ({max_t:.0f}s) reached: {cap_hit} runs ({cap_hit/r['runs']*100:.0f}%)")
    print(f"  Best:{r['best']:.1f}s Worst:{r['worst']:.1f}s "
          f"Avg:{r['avg']:.1f}s Med:{r['median']:.1f}s")
    print(f"  P90:{r['p90']:.1f}s P75:{r['p75']:.1f}s P25:{r['p25']:.1f}s")
    buckets = [0, 1, 2, 3, 5, 8, 12, 18, 25, 35, 50, 70, 100, 999]
    print("  Histogram (seconds):")
    for i in range(len(buckets) - 1):
        c = sum(1 for t in r["times"] if buckets[i] <= t < buckets[i+1])
        pct = c / r['runs'] * 100
        bar = "#" * int(c * 50 / max(r['runs'], 1))
        print(f"    {buckets[i]:>3}-{buckets[i+1]:<4}s: {c:>4} ({pct:>4.0f}%) {bar}")
    print("=" * 60)


if __name__ == "__main__":
    main()
