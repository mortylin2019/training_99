#!/usr/bin/env python3
"""
Capture the last N frames before death for debugging AI failures.

Usage:
  python tools/capture_death_log.py --ai ai_beam --seed 42 --frames 30
  python tools/capture_death_log.py --ai ai_beam --seed 42 --frames 60 --difficulty 2
"""
import sys, os, json, argparse
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hijack_tools'))

import numpy as np
from hijack_tools.simulator.engine import GameSimulator
from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE


def load_ai(name):
    if name == 'ai_beam':
        from ai_beam import BeamAI; return BeamAI
    if name == 'ai_basic':
        from ai_basic import BasicAI; return BasicAI
    if name == 'ai_nn':
        from ai_nn import NNBoostedBeamAI; return NNBoostedBeamAI
    raise ValueError(f"Unknown AI: {name}")


def capture_death(ai_name, seed, difficulty, max_frames, log_frames):
    """Run simulation, capture last N frames before death."""
    AI = load_ai(ai_name)
    ai = AI(vel_table=VEL_TABLE, accel_table=ACCEL_TABLE)
    sim = GameSimulator(difficulty=difficulty, seed=seed)

    buffer = deque(maxlen=log_frames)

    for _ in range(max_frames):
        bullets = sim.get_visible_bullets()
        bits = ai.decide(sim.px, sim.py, bullets) if bullets else 0

        # Record frame state
        frame = {
            'frame': sim.frame,
            'px': sim.px, 'py': sim.py,
            'bits': bits,
            'n_bullets': len(bullets),
            'patterns': {},
        }

        # Nearest bullet distance
        nearest_d2 = float('inf')
        for b in bullets:
            d2 = (b.x - sim.px)**2 + (b.y - sim.py)**2
            if d2 < nearest_d2:
                nearest_d2 = d2
                frame['nearest_bullet'] = {'x': b.x, 'y': b.y, 'd': d2**0.5,
                                             'angle': b.angle_index, 'type': b.type}

        # Bullet type distribution
        type_counts = {}
        for b in bullets:
            t = b.type
            type_counts[f'T{t}'] = type_counts.get(f'T{t}', 0) + 1
        frame['bullet_types'] = type_counts

        # Bullets in danger zone (<30px)
        danger_count = 0
        for b in bullets:
            d2 = (b.x - sim.px)**2 + (b.y - sim.py)**2
            if d2 < 900:  # 30^2
                danger_count += 1
        frame['bullets_nearby'] = danger_count

        buffer.append(frame)
        alive, _ = sim.step(bits)
        if not alive:
            break

    # Add death info
    death_frame = {
        'death_frame': sim.frame,
        from hijack_tools.simulator.config import FPS as SIM_FPS
'survival_s': sim.frame / SIM_FPS,
        'config': {
            'ai': ai_name,
            'seed': seed,
            'difficulty': difficulty,
            'px_at_death': sim.px,
            'py_at_death': sim.py,
        }
    }

    return list(buffer), death_frame


def analyze(frames, death):
    """Print human-readable analysis of the death."""
    print(f"\n{'='*70}")
    print(f"  DEATH ANALYSIS — {death['config']['ai']} seed={death['config']['seed']}")
    print(f"  Difficulty {death['config']['difficulty']}, "
          f"Died at frame {death['death_frame']} ({death['survival_s']:.1f}s)")
    print(f"  Position at death: ({death['config']['px_at_death']}, "
          f"{death['config']['py_at_death']})")
    print(f"{'='*70}")

    if not frames:
        print("No frames captured.")
        return

    print(f"\n  Last {len(frames)} frames:")
    print(f"  {'Frame':>6} {'X':>4} {'Y':>4} {'Bits':>4} {'N':>3} "
          f"{'Near':>4} {'Nearest':>8} {'Types'}")

    for f in frames:
        nb = f.get('nearest_bullet', {})
        dist = nb.get('d', 999)
        types_str = ' '.join(f'{k}={v}' for k, v in
                            sorted(f.get('bullet_types', {}).items()))
        print(f"  {f['frame']:>6} {f['px']:>4} {f['py']:>4} {f['bits']:>4} "
              f"{f['n_bullets']:>3} {f['bullets_nearby']:>4} "
              f"{dist:>7.1f}px  {types_str}")

    # Summary stats
    if frames:
        bits_used = set(f['bits'] for f in frames)
        print(f"\n  Bits used: {sorted(bits_used)}")
        nearby = [f['bullets_nearby'] for f in frames]
        print(f"  Bullets <30px: min={min(nearby)} max={max(nearby)} "
              f"avg={np.mean(nearby):.1f}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Capture death log for debugging')
    p.add_argument('--ai', default='ai_beam')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--difficulty', type=int, default=1)
    p.add_argument('--max-frames', type=int, default=16000)
    p.add_argument('--frames', type=int, default=30,
                   help='Number of frames to capture before death')
    p.add_argument('--output', default=None, help='Save JSON to file')
    args = p.parse_args()

    frames, death = capture_death(args.ai, args.seed, args.difficulty,
                                  args.max_frames, args.frames)
    analyze(frames, death)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump({'death': death, 'frames': frames}, f, indent=2)
        print(f"\nSaved: {args.output}")
