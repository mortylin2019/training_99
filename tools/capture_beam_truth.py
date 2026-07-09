#!/usr/bin/env python3
"""
Gate 0: Capture Python beam search ground truth for C port validation.

Runs the simulator for N seeds, records every beam search decision:
  (px, py, bullet_xs, bullet_ys, bullet_angles, beam_result_idx)

Saved as tests/beam_truth.npz — immutable reference for C comparison.

Usage:
  python tools/capture_beam_truth.py --seeds 100 --difficulty 1
"""
import sys, os, argparse
import numpy as np
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hijack_tools'))

from hijack_tools.simulator.engine import GameSimulator
from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE
from hijack_tools.ai_beam import BeamAI, _beam_search, _score_pos, _max_gap_move
import hijack_tools.algo_config as cfg


def capture(seeds=100, difficulty=1, max_frames=4000):
    """Run simulator, capture every beam search decision."""
    ai = BeamAI(vel_table=VEL_TABLE, accel_table=ACCEL_TABLE)
    records = []
    pbar = tqdm(range(seeds), desc="Capturing", unit="seed")

    for seed in pbar:
        sim = GameSimulator(difficulty=difficulty, seed=seed * 12345)
        n_frames = 0
        n_decisions = 0

        for _ in range(max_frames):
            bullets = sim.get_visible_bullets()
            if not bullets:
                alive, _ = sim.step(0)
                if not alive:
                    break
                n_frames += 1
                continue

            paths = ai._predict(bullets)
            beam_idx = int(_beam_search(float(sim.px), float(sim.py), paths))

            xs = np.array([b.x for b in bullets], dtype=np.float32)
            ys = np.array([b.y for b in bullets], dtype=np.float32)
            ang = np.array([b.angle_index for b in bullets], dtype=np.int16)

            records.append({
                'px': sim.px, 'py': sim.py,
                'n_bullets': len(bullets),
                'xs': xs, 'ys': ys, 'angles': ang,
                'beam_idx': beam_idx,
            })

            bits = int(cfg.BITS[max(beam_idx, 0) % len(cfg.BITS)])
            alive, _ = sim.step(bits)
            n_frames += 1
            n_decisions += 1
            if not alive:
                break

        surv = sim.frame / 80.0
        pbar.set_postfix(samples=len(records), last_surv=f"{surv:.0f}s")

    return records


def save_npz(records, path):
    """Save records as a single compressed .npz with flat arrays."""
    total = len(records)
    total_bullets = sum(r['n_bullets'] for r in records)

    px = np.zeros(total, dtype=np.float32)
    py = np.zeros(total, dtype=np.float32)
    n_bullets = np.zeros(total, dtype=np.int16)
    beam_idx = np.zeros(total, dtype=np.int32)
    bullet_xs = np.zeros(total_bullets, dtype=np.float32)
    bullet_ys = np.zeros(total_bullets, dtype=np.float32)
    bullet_angles = np.zeros(total_bullets, dtype=np.int16)
    offsets = np.zeros(total, dtype=np.int32)

    cursor = 0
    for i, r in enumerate(records):
        px[i] = r['px']
        py[i] = r['py']
        n_bullets[i] = r['n_bullets']
        beam_idx[i] = r['beam_idx']
        offsets[i] = cursor
        n = r['n_bullets']
        bullet_xs[cursor:cursor + n] = r['xs']
        bullet_ys[cursor:cursor + n] = r['ys']
        bullet_angles[cursor:cursor + n] = r['angles']
        cursor += n

    np.savez_compressed(path,
        px=px, py=py, n_bullets=n_bullets,
        beam_idx=beam_idx,
        bullet_xs=bullet_xs, bullet_ys=bullet_ys, bullet_angles=bullet_angles,
        bullet_offsets=offsets,
        total_samples=total, total_bullets=total_bullets,
        version=1,
    )
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"\nSaved: {path} ({size_mb:.1f} MB)")
    print(f"  {total} samples, {total_bullets} bullets ({total_bullets / max(total, 1):.1f} avg/frame)")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Capture beam search ground truth")
    p.add_argument("--seeds", type=int, default=100)
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=4000)
    p.add_argument("--output", type=str, default="tests/beam_truth.npz")
    args = p.parse_args()

    print(f"Capturing beam truth: {args.seeds} seeds, difficulty={args.difficulty}")
    records = capture(args.seeds, args.difficulty, args.max_frames)
    save_npz(records, args.output)
