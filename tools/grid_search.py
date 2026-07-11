#!/usr/bin/env python3
"""
Grid search AI parameters via simulator — find the best config.

Runs a parameter grid over the simulator (fast, deterministic), collects
survival times + speed profiles, then plots results.

Usage:
  python tools/grid_search.py --ai ai_beam --seeds 10 --max-frames 16000
  python tools/grid_search.py --ai ai_beam --seeds 5 --max-frames 8000 --quick  # fast scan
"""
import sys, os, time, itertools, argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hijack_tools'))


# ── Parameter grid ────────────────────────────────────────────────────────────

# Edit this to search different parameter ranges.
# Each combo = cartesian product of all values.
GRID = {
    'BEAM_WIDTH':      [20, 30, 40, 50],
    'BEAM_DEPTH':      [12, 16, 20],
    'CHECK_EVERY':     [3, 4, 5, 6],
    'DANGER_BASE':     [1000, 2000, 4000],
    'WALL_MARGIN':     [20, 40, 60],
    'SAFETY_MARGIN':   [0, 2, 4],
    'SHORTCUT_DISTANCE': [120, 200, 0],
    'EARLY_EXIT_BUFFER': [10000, 50000],
    'EARLY_EXIT_ENABLED': [True, False],
    'PARTIAL_SORT_ENABLED': [True],
    'CENTER_PULL_ENABLED': [True, False],
    'WALL_PENALTY_ENABLED': [True, False],
}

# Quick mode — test the most impactful axes first
GRID_QUICK = {
    'BEAM_WIDTH':      [20, 30, 50],
    'BEAM_DEPTH':      [12, 20],
    'CHECK_EVERY':     [4, 6],
    'DANGER_BASE':     [1000, 2000],
    'SHORTCUT_DISTANCE': [120, 200],
    'CENTER_PULL_ENABLED': [True, False],
}


# ── Worker (runs in subprocess via ProcessPoolExecutor) ──────────────────────

def _load_ai(name):
    if name == 'ai_beam':
        from ai_beam import BeamAI
        return BeamAI
    if name == 'ai_basic':
        from ai_basic import BasicAI
        return BasicAI
    if name == 'ai_nn':
        from ai_nn import NNBoostedBeamAI
        return NNBoostedBeamAI
    raise ValueError(f"Unknown AI: {name}")


def _run_combo(args):
    """Run one (param_combo, seed) — picklable for ProcessPoolExecutor."""
    ai_name, params, difficulty, max_frames, seed = args

    # Modify algo_config BEFORE importing ai_beam (fresh import in subprocess)
    import hijack_tools.algo_config as cfg
    for key, val in params.items():
        if val == 0 and key == 'SHORTCUT_DISTANCE':
            # Special: 0 = disable shortcut entirely
            cfg.SHORTCUT_ENABLED = False
        elif key == 'SHORTCUT_DISTANCE':
            cfg.SHORTCUT_DISTANCE = val
            cfg.SHORTCUT_ENABLED = True
        else:
            setattr(cfg, key, val)

    # Now import AI (reads the modified config)
    AI = _load_ai(ai_name)
    from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE
    ai = AI(vel_table=VEL_TABLE, accel_table=ACCEL_TABLE)

    from hijack_tools.simulator.engine import GameSimulator
    sim = GameSimulator(difficulty=difficulty, seed=seed)

    # Warmup: 2 full runs to trigger JIT compilation (results discarded)
    for warm_seed in [99991, 99992]:
        sim_warm = GameSimulator(difficulty=difficulty, seed=warm_seed)
        for _ in range(500):
            b = sim_warm.get_visible_bullets()
            bits = ai.decide(sim_warm.px, sim_warm.py, b) if b else 0
            alive, _ = sim_warm.step(bits)
            if not alive:
                break

    # Timed run
    t0 = time.perf_counter()
    for _ in range(max_frames):
        b = sim.get_visible_bullets()
        bits = ai.decide(sim.px, sim.py, b) if b else 0
        alive, _ = sim.step(bits)
        if not alive:
            break
    elapsed = time.perf_counter() - t0

    survival = sim.frame / 80.0  # 80 FPS

    return {
        'survival': survival,
        'frames': sim.frame,
        'time': elapsed,
        'params': dict(params),
    }


# ── Grid search ──────────────────────────────────────────────────────────────

def grid_search(ai_name, grid, seeds, difficulty, max_frames, workers):
    """Run all parameter combos × seeds in parallel."""
    combos = []
    keys = list(grid.keys())
    for values in itertools.product(*grid.values()):
        combo = dict(zip(keys, values))
        for seed in range(seeds):
            combos.append((ai_name, combo, difficulty, max_frames, seed * 12345))

    print(f"Grid: {len(grid)} params, {len(combos)} total runs "
          f"({len(combos)//seeds} combos × {seeds} seeds)")

    results = []
    try:
        from tqdm import tqdm
        pbar = tqdm(total=len(combos), desc="Grid search", unit="run")
    except ImportError:
        pbar = None

    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(_run_combo, combos):
            results.append(r)
            if pbar:
                best = max(r2['survival'] for r2 in results) if results else 0
                pbar.set_postfix(best=f"{best:.0f}s")
                pbar.update(1)

    if pbar:
        pbar.close()
    return results


# ── Aggregate + Plot ─────────────────────────────────────────────────────────

def aggregate(results):
    """Group by parameter combo, compute mean/std survival + speed."""
    groups = defaultdict(list)
    for r in results:
        key = tuple(sorted(r['params'].items()))
        groups[key].append(r)

    rows = []
    for key, group in groups.items():
        survs = np.array([g['survival'] for g in group])
        times = np.array([g['time'] for g in group])
        frames = np.array([g['frames'] for g in group])
        rows.append({
            'params': dict(key),
            'avg_survival': np.mean(survs),
            'median_survival': np.median(survs),
            'p25_survival': np.percentile(survs, 25),
            'p75_survival': np.percentile(survs, 75),
            'best_survival': np.max(survs),
            'worst_survival': np.min(survs),
            'avg_time': np.mean(times),
            'avg_speed': np.mean(frames / np.maximum(times, 0.001)),
            'seeds': len(group),
        })

    rows.sort(key=lambda r: -r['avg_survival'])
    return rows


def print_table(rows, top_n=20):
    """Print top results as a formatted table."""
    print(f"\n{'='*80}")
    print(f"  Top {min(top_n, len(rows))} configurations (by avg survival)")
    print(f"{'='*80}")
    header = (f"{'Rank':>4}  {'Avg':>6}  {'Med':>6}  {'P25':>6}  {'P75':>6}  "
              f"{'Best':>6}  {'Worst':>6}  {'FPS':>6}  Params")
    print(header)
    print("-" * len(header))

    for i, row in enumerate(rows[:top_n]):
        params_str = "  ".join(f"{k}={v}" for k, v in row['params'].items())
        print(f"{i+1:>4}  {row['avg_survival']:>5.1f}s  {row['median_survival']:>5.1f}s  "
              f"{row['p25_survival']:>5.1f}s  {row['p75_survival']:>5.1f}s  "
              f"{row['best_survival']:>5.1f}s  {row['worst_survival']:>5.1f}s  "
              f"{row['avg_speed']:>5.0f}   {params_str}")


def plot_results(rows, output_dir="."):
    """Generate plots: survival heatmap, speed vs survival, parameter impact."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib not installed — skipping plots.")
        print("Install: pip install matplotlib")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Figure 1: Survival heatmap (BEAM_WIDTH × BEAM_DEPTH)
    # Group by (WIDTH, DEPTH), average over other params
    width_depth = defaultdict(list)
    for row in rows:
        p = row['params']
        w = p.get('BEAM_WIDTH', p.get('BEAM_DEPTH', '?'))
        d = p.get('BEAM_DEPTH', p.get('CHECK_EVERY', '?'))
        if isinstance(w, int) and isinstance(d, int):
            width_depth[(w, d)].append(row['avg_survival'])

    if width_depth:
        ws = sorted(set(k[0] for k in width_depth))
        ds = sorted(set(k[1] for k in width_depth))
        hm = np.zeros((len(ds), len(ws)))
        for (w, d), survs in width_depth.items():
            hm[ds.index(d), ws.index(w)] = np.mean(survs)

        fig, ax = plt.subplots(figsize=(8, 5))
        im = ax.imshow(hm, cmap='RdYlGn', aspect='auto')
        ax.set_xticks(range(len(ws))); ax.set_xticklabels(ws)
        ax.set_yticks(range(len(ds))); ax.set_yticklabels(ds)
        ax.set_xlabel('BEAM_WIDTH'); ax.set_ylabel('BEAM_DEPTH')
        ax.set_title('Avg Survival (s) — Beam Width × Depth')
        for i in range(len(ds)):
            for j in range(len(ws)):
                ax.text(j, i, f'{hm[i,j]:.0f}', ha='center', va='center',
                        fontsize=9, fontweight='bold')
        plt.colorbar(im, ax=ax, label='seconds')
        fig.tight_layout()
        fig.savefig(f'{output_dir}/grid_beam_width_depth.png', dpi=120)
        plt.close(fig)

    # Figure 2: Parameter impact — avg survival per parameter value
    param_keys = set()
    for row in rows:
        param_keys.update(row['params'].keys())
    param_keys = sorted(param_keys)

    fig, axes = plt.subplots(1, len(param_keys), figsize=(5 * len(param_keys), 4),
                             squeeze=False)
    for ax_i, key in enumerate(param_keys):
        ax = axes[0, ax_i]
        vals = defaultdict(list)
        for row in rows:
            v = row['params'].get(key)
            if v is not None:
                vals[v].append(row['avg_survival'])
        xv = sorted(vals.keys())
        yv = [np.mean(vals[v]) for v in xv]
        ye = [np.std(vals[v]) for v in xv]
        ax.bar(range(len(xv)), yv, yerr=ye, capsize=5, color='steelblue', alpha=0.8)
        ax.set_xticks(range(len(xv)))
        ax.set_xticklabels([str(v) for v in xv], rotation=30 if len(xv) > 4 else 0,
                           ha='right' if len(xv) > 4 else 'center')
        ax.set_ylabel('Avg Survival (s)')
        ax.set_title(key)
        ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(f'{output_dir}/grid_param_impact.png', dpi=120)
    plt.close(fig)

    # Figure 3: Speed vs Survival tradeoff
    fig, ax = plt.subplots(figsize=(8, 5))
    xs = [r['avg_speed'] for r in rows]
    ys = [r['avg_survival'] for r in rows]
    sc = ax.scatter(xs, ys, c=ys, cmap='RdYlGn', s=60, alpha=0.7)
    ax.set_xlabel('Avg Speed (frames/sec)')
    ax.set_ylabel('Avg Survival (s)')
    ax.set_title('Speed vs Survival Tradeoff')
    ax.grid(alpha=0.3)
    plt.colorbar(sc, ax=ax, label='survival (s)')
    fig.tight_layout()
    fig.savefig(f'{output_dir}/grid_speed_vs_survival.png', dpi=120)
    plt.close(fig)

    print(f"\nPlots saved to {output_dir}/")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Grid search AI parameters via simulator")
    p.add_argument('--ai', default='ai_beam', help='AI algorithm name')
    p.add_argument('--seeds', type=int, default=10, help='Seeds per parameter combo')
    p.add_argument('--difficulty', type=int, default=1, help='1=Normal, 2=Hard')
    p.add_argument('--max-frames', type=int, default=16000, help='Max frames (200s at 80fps)')
    p.add_argument('--workers', type=int, default=os.cpu_count() or 4)
    p.add_argument('--quick', action='store_true', help='Use smaller grid for fast scan')
    p.add_argument('--output', default='grid_results', help='Output directory for plots')
    args = p.parse_args()

    grid = GRID_QUICK if args.quick else GRID
    total_combos = 1
    for v in grid.values():
        total_combos *= len(v)
    est_time = total_combos * args.seeds * (args.max_frames / 80.0 / 4)  # rough estimate
    print(f"Parameters: {list(grid.keys())}")
    print(f"Combos: {total_combos} × {args.seeds} seeds = {total_combos * args.seeds} runs")
    print(f"Est. time: ~{est_time/60:.0f} min ({args.workers} workers)")

    results = grid_search(args.ai, grid, args.seeds, args.difficulty,
                          args.max_frames, args.workers)
    rows = aggregate(results)

    if not rows:
        print("No results.")
        return

    print_table(rows, top_n=20)
    plot_results(rows, args.output)

    best = rows[0]
    print(f"\nBest config: {best['params']}")
    print(f"  Survival: {best['avg_survival']:.1f}s (±{best['std_survival']:.1f}) "
          f"[{best['worst_survival']:.1f}–{best['best_survival']:.1f}]")
    print(f"  Speed: {best['avg_speed']:.0f} fps")


if __name__ == '__main__':
    main()
