#!/usr/bin/env python3
"""
Generate NN training data with RESUME support via sharded .npz files.

Each seed saved independently → crash-safe, memory-efficient, gzip-compressed.
Crash mid-save? Only that seed's file is lost (re-generated on resume).
Power loss? meta.json rebuilt from shard directory with --rebuild-meta.

Usage:
  python3 tools/gen_training_data.py --seeds 1000 --width 50 --workers 16
  # If interrupted: re-run same command — resumes from meta.json.
  python3 tools/gen_training_data.py --combine  # merge shards → combined.npz for training
  python3 tools/gen_training_data.py --rebuild-meta  # fix corrupted meta.json from shards
"""
import sys, os, time, json, argparse
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

# Ensure hijack_tools is importable from project root (needed by subprocess workers via fork)
_PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, _PROJ_ROOT)
from hijack_tools.simulator.config import FPS as SIM_FPS
# ai_beam.py uses bare `from algo_config import ...` — add hijack_tools/ to sys.path
sys.path.insert(0, os.path.join(_PROJ_ROOT, 'hijack_tools'))

SAVE_DIR = "training_data"
SHARD_DIR = os.path.join(SAVE_DIR, "shards")
META_PATH = os.path.join(SAVE_DIR, "meta.json")
FRAMES_PER_SAVE = 4

# ── Shard I/O ──────────────────────────────────────────────────────────────────

def save_shard(seed_idx, tagged, survival, shard_dir=None):
    """Atomically save one seed's training samples as compressed .npz.

    Format per frame:
      px: float32[N]          py: float32[N]
      moves: int8[N]          survival_remaining: float32[N]
      n_bullets: int16[N]     # how many bullets this frame
      bullet_xs: float32[T]   # all bullets from all frames, flattened
      bullet_ys: float32[T]
      bullet_angles: int16[T]
    """
    if shard_dir is None:
        shard_dir = SHARD_DIR
    os.makedirs(shard_dir, exist_ok=True)

    if not tagged:
        return 0

    n = len(tagged)
    px = np.array([t[0] for t in tagged], dtype=np.float32)
    py = np.array([t[1] for t in tagged], dtype=np.float32)
    moves = np.array([t[3] for t in tagged], dtype=np.int8)
    sr = np.array([t[4] for t in tagged], dtype=np.float32)

    # Flatten all bullets across all frames — compact storage, no padding waste
    all_bx, all_by, all_ba = [], [], []
    n_bullets = np.zeros(n, dtype=np.int16)
    for i, (_, _, state, _, _) in enumerate(tagged):
        n_bullets[i] = len(state)
        for bx, by, ang in state:
            all_bx.append(bx)
            all_by.append(by)
            all_ba.append(ang)

    tmp = os.path.join(shard_dir, f".seed_{seed_idx:04d}.npz")
    dst = os.path.join(shard_dir, f"seed_{seed_idx:04d}.npz")
    np.savez_compressed(tmp,
        seed=seed_idx, n_frames=n,
        px=px, py=py, moves=moves, survival_remaining=sr,
        n_bullets=n_bullets,
        bullet_xs=np.array(all_bx, dtype=np.float32),
        bullet_ys=np.array(all_by, dtype=np.float32),
        bullet_angles=np.array(all_ba, dtype=np.int16),
        total_survival=np.float32(survival),
    )
    os.replace(tmp, dst)  # atomic on Linux — no half-written files
    return n


def load_meta():
    """Return (completed_seed_set, survivals_list, config_dict)."""
    if os.path.exists(META_PATH):
        with open(META_PATH, 'r') as f:
            meta = json.load(f)
        return (set(meta.get('completed_seeds', [])),
                meta.get('survivals', []),
                meta.get('config', {}))
    return set(), [], {}


def save_meta(completed_seeds, survivals, config):
    """Atomic save of progress metadata."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    tmp = META_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump({
            'config': config,
            'completed_seeds': sorted(completed_seeds),
            'survivals': survivals,
            'version': 2,
        }, f)
    os.replace(tmp, META_PATH)


# ── Seed runner (runs in ProcessPoolExecutor subprocess) ───────────────────────

def run_seed(args):
    """Run one seed, save its shard, return (seed_idx, survival, n_samples)."""
    seed_idx, rng_seed, difficulty, max_frames, width, depth, check_every, shard_dir = args

    # Import inside function for clean process isolation
    import hijack_tools.algo_config as cfg
    cfg.BEAM_WIDTH = width
    cfg.BEAM_DEPTH = depth
    cfg.CHECK_EVERY = check_every

    from hijack_tools.simulator.engine import GameSimulator
    from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE
    from hijack_tools.ai_beam import BeamAI

    ai = BeamAI(vel_table=VEL_TABLE, accel_table=ACCEL_TABLE)
    sim = GameSimulator(difficulty=difficulty, seed=rng_seed)
    samples = []

    try:
        for frame in range(max_frames):
            # Record training sample every FRAMES_PER_SAVE frames
            if frame % FRAMES_PER_SAVE == 0 and sim.bullet_count > 0:
                bullets = sim.get_visible_bullets()
                if bullets:
                    state = [(b.x, b.y, b.angle_index) for b in bullets]
                    bits = ai.decide(sim.px, sim.py, bullets)
                    samples.append((sim.px, sim.py, state, bits))

            bullets = sim.get_visible_bullets()
            bits = ai.decide(sim.px, sim.py, bullets) if bullets else 0
            alive, _ = sim.step(bits)
            if not alive:
                break
    except Exception as e:
        print(f"Seed {seed_idx} error: {e}")

    survival = sim.frame / SIM_FPS

    # Tag each sample with remaining survival (for value head target)
    tagged = [(px, py, state, move, survival - (i * FRAMES_PER_SAVE / SIM_FPS))
              for i, (px, py, state, move) in enumerate(samples)]

    n = save_shard(seed_idx, tagged, survival, shard_dir)
    return seed_idx, survival, n


# ── Combine mode: merge shards into single training .npz ───────────────────────

def combine_shards(shard_dir=None, output_path=None, n_seeds=None):
    """Read all seed_NNNN.npz shards → single combined.npz for NN training.

    Combined format adds bullet_offsets for efficient per-frame slicing:
      bullet_offsets: int32[N]  — offset into flat bullet arrays for frame i
    """
    shard_dir = shard_dir or SHARD_DIR
    output_path = output_path or os.path.join(SAVE_DIR, "combined.npz")

    if not os.path.isdir(shard_dir):
        print(f"No shard directory: {shard_dir}")
        return 0

    available = sorted([
        int(f.replace("seed_", "").replace(".npz", ""))
        for f in os.listdir(shard_dir)
        if f.startswith("seed_") and f.endswith(".npz")
    ])
    if n_seeds:
        available = [s for s in available if s < n_seeds]

    if not available:
        print("No shards found.")
        return 0

    print(f"Combining {len(available)} shards → {output_path} ...")

    all_px, all_py, all_moves, all_sr = [], [], [], []
    all_nb, all_bx, all_by, all_ba = [], [], [], []

    for seed in tqdm(available):
        d = np.load(os.path.join(shard_dir, f"seed_{seed:04d}.npz"))
        all_px.append(d['px']); all_py.append(d['py'])
        all_moves.append(d['moves']); all_sr.append(d['survival_remaining'])
        all_nb.append(d['n_bullets'])
        all_bx.append(d['bullet_xs']); all_by.append(d['bullet_ys'])
        all_ba.append(d['bullet_angles'])

    px = np.concatenate(all_px); py = np.concatenate(all_py)
    moves = np.concatenate(all_moves); sr = np.concatenate(all_sr)
    n_bullets = np.concatenate(all_nb)
    bullet_xs = np.concatenate(all_bx); bullet_ys = np.concatenate(all_by)
    bullet_angles = np.concatenate(all_ba)

    # Per-sample starting offset for slicing flat bullet arrays
    offsets = np.zeros(len(n_bullets), dtype=np.int32)
    offsets[1:] = np.cumsum(n_bullets[:-1])

    np.savez_compressed(output_path,
        px=px, py=py, moves=moves, survival_remaining=sr,
        n_bullets=n_bullets,
        bullet_xs=bullet_xs, bullet_ys=bullet_ys, bullet_angles=bullet_angles,
        bullet_offsets=offsets,
    )

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    total_b = int(n_bullets.sum())
    print(f"  {len(px)} samples, {total_b} bullets ({total_b / max(len(px), 1):.1f} avg/frame)")
    print(f"  {size_mb:.1f} MB saved → {output_path}")
    return len(px)


# ── Meta rebuild: scan shard directory, reconstruct meta.json ──────────────────

def rebuild_meta(shard_dir=None):
    """Scan shard directory and rebuild meta.json from surviving .npz files."""
    shard_dir = shard_dir or SHARD_DIR
    if not os.path.isdir(shard_dir):
        print(f"No shard directory: {shard_dir}")
        return

    completed = []
    survivals = []
    for f in sorted(os.listdir(shard_dir)):
        if not f.startswith("seed_") or not f.endswith(".npz"):
            continue
        seed = int(f.replace("seed_", "").replace(".npz", ""))
        try:
            d = np.load(os.path.join(shard_dir, f))
            completed.append(seed)
            survivals.append(float(d['total_survival']))
        except Exception as e:
            print(f"  Skip corrupt {f}: {e}")

    config = {"rebuilt": True}
    save_meta(completed, survivals, config)
    if survivals:
        print(f"Rebuilt meta: {len(completed)} seeds, "
              f"avg {np.mean(survivals):.1f}s, "
              f"best {max(survivals):.1f}s, worst {min(survivals):.1f}s")
    else:
        print("No valid shards found.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Generate NN training data (sharded .npz, crash-safe)")
    p.add_argument("--seeds", type=int, default=1000)
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--width", type=int, default=50)
    p.add_argument("--depth", type=int, default=20)
    p.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    p.add_argument("--max-frames", type=int, default=4000)
    p.add_argument("--combine", action="store_true",
                   help="Combine all shards into a single training .npz")
    p.add_argument("--combine-output", type=str, default=None,
                   help="Path for combined .npz (default: training_data/combined.npz)")
    p.add_argument("--rebuild-meta", action="store_true",
                   help="Rebuild meta.json from shard directory (fix corruption)")
    args = p.parse_args()

    # ── Sub-commands ──
    if args.rebuild_meta:
        rebuild_meta()
        return

    if args.combine:
        combine_shards(SHARD_DIR, args.combine_output, args.seeds)
        return

    # ── Main generation mode ──
    os.makedirs(SHARD_DIR, exist_ok=True)

    config = {
        'width': args.width, 'depth': args.depth,
        'difficulty': args.difficulty, 'total_seeds': args.seeds,
        'max_frames': args.max_frames,
    }

    completed_seeds, survivals, prev_config = load_meta()
    pending = [s for s in range(args.seeds) if s not in completed_seeds]

    print(f"Config: width={args.width} depth={args.depth} difficulty={args.difficulty} "
          f"max_frames={args.max_frames} workers={args.workers}")
    print(f"Resuming: {len(completed_seeds)}/{args.seeds} done, {len(pending)} remaining")
    print(f"Shard dir: {SHARD_DIR}")

    if not pending:
        print("All seeds complete! Run --combine to build training file.")
        return

    # 7-tuple: (seed_idx, rng_seed, difficulty, max_frames, width, depth, check_every, shard_dir)
    # seed_idx = identifier (0..999), rng_seed = seed_idx * 12345 (deterministic RNG)
    tasks = [(seed, seed * 12345, args.difficulty, args.max_frames,
              args.width, args.depth, 4, SHARD_DIR) for seed in pending]

    t0 = time.time()
    save_interval = max(10, len(pending) // 20)  # meta.json saved every ~5%
    batch_since_save = 0

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for seed_idx, survival, n_samples in tqdm(
            pool.map(run_seed, tasks),
            total=len(pending), desc="Generating"
        ):
            completed_seeds.add(seed_idx)
            survivals.append(survival)
            batch_since_save += 1

            if batch_since_save >= save_interval:
                save_meta(completed_seeds, survivals, config)
                batch_since_save = 0

    # Final atomic save
    save_meta(completed_seeds, survivals, config)

    elapsed = time.time() - t0
    print(f"\n{len(pending)} seeds in {elapsed:.0f}s "
          f"({elapsed / max(len(pending), 1):.1f}s/seed)")
    print(f"Total: {len(survivals)} seeds completed")
    if survivals:
        print(f"Avg survival: {np.mean(survivals):.1f}s   "
              f"Best: {max(survivals):.1f}s   Worst: {min(survivals):.1f}s")
        print(f"\nRun --combine to merge shards for training.")


if __name__ == "__main__":
    main()
