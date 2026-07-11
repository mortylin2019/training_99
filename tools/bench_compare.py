#!/usr/bin/env python3
"""
tools/bench_compare.py — Compare beam search vs MCTS on the simulator.
Run: python tools/bench_compare.py [--runs 30] [--ai ai_beam,ai_mcts]
"""
import sys, argparse, time, os, numpy as np
sys.path.insert(0, ".")
sys.path.insert(0, "hijack_tools")
_BEAM_CORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "hijack_tools", "beam_core")
if os.path.isdir(_BEAM_CORE_DIR) and _BEAM_CORE_DIR not in sys.path:
    sys.path.insert(0, _BEAM_CORE_DIR)

from hijack_tools.simulator.engine import GameSimulator
from hijack_tools.simulator.tables import VEL_TABLE
from ai_beam import BeamAI
from ai_mcts import MctSAI
import hijack_tools.algo_config as cfg


def run_one(ai_cls, difficulty, seed, max_frames=40000):
    ai = ai_cls(vel_table=VEL_TABLE)
    sim = GameSimulator(difficulty=difficulty, seed=seed)
    for _ in range(max_frames):
        bullets = sim.get_visible_bullets()
        move = ai.decide(sim.px, sim.py, bullets) if bullets else 0
        alive, _ = sim.step(move)
        if not alive:
            break
    from hijack_tools.simulator.config import FPS as SIM_FPS
return sim.frame / SIM_FPS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=10)
    p.add_argument("--difficulty", type=int, default=1, choices=[0, 1, 2, 3],
                   help="0=Easy, 1=Normal, 2=Hard, 3=Lunatic")
    p.add_argument("--ai", default="ai_beam,ai_mcts")
    p.add_argument("--max-frames", type=int, default=40000)
    args = p.parse_args()

    ai_names = [a.strip() for a in args.ai.split(",")]
    diff_name = {0: "Easy", 1: "Normal", 2: "Hard", 3: "Lunatic"}[args.difficulty]

    ai_map = {"ai_beam": ("beam W=12", BeamAI), "ai_mcts": ("MCTS 1000iter", MctSAI)}

    print(f"=== {diff_name} difficulty, {args.runs} runs each ===")
    for name in ai_names:
        label, cls = ai_map[name]
        survs = []
        t0 = time.perf_counter()
        for i in range(args.runs):
            s = run_one(cls, args.difficulty, seed=i * 12345,
                        max_frames=args.max_frames)
            survs.append(s)
            if i % 5 == 0 or i == args.runs - 1:
                print(f"  {label} [{i+1}/{args.runs}] "
                      f"last={s:.1f}s running_med={np.median(survs[:i+1]):.1f}s")
        dt = time.perf_counter() - t0
        print(f"  {label}: med={np.median(survs):.1f}s avg={np.mean(survs):.1f}s "
              f"best={max(survs):.1f}s worst={min(survs):.1f}s  [{dt:.0f}s]\n")


if __name__ == "__main__":
    main()
