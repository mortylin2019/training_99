"""
profile_ai.py — Profile AI algorithm performance.

Usage:
    python hijack_tools/profile_ai.py                  # profile ai_direct
    python hijack_tools/profile_ai.py --ai ai_beam      # profile another algo
    python hijack_tools/profile_ai.py --frames 10000    # simulate N frames
    python hijack_tools/profile_ai.py --bullets 50      # bullet count
"""

import time
import sys
import random
import math
import cProfile
import pstats
import io
from dataclasses import dataclass
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


@dataclass
class FakeBullet:
    """Fake bullet for profiling without the real game."""
    raw_x: int = 0
    raw_y: int = 0
    angle_index: int = 0
    active: int = 1
    type: int = 0    # 0=Normal
    timer: int = 0
    index: int = 0
    vx: int = 0
    vy: int = 0

    @property
    def x(self) -> float:
        return (self.raw_x >> 6) - 4

    @property
    def y(self) -> float:
        return (self.raw_y >> 6) - 4


def load_ai(name):
    if name == "ai_direct":
        from ai_direct import SuperiorAI
        return SuperiorAI
    if name == "ai_beam":
        from ai_beam import BeamAI
        return BeamAI
    if name == "ai_numba":
        from ai_beam import BeamAI
        return BeamAI  # legacy alias
    raise ValueError(f"Unknown AI: {name}")


def generate_fake_vel_table():
    """Generate fake 64-angle velocity table mimicking the game."""
    table = []
    for i in range(64):
        angle = i * 2 * math.pi / 64
        speed = 160  # raw units, ~2.5 px/frame
        vx = int(math.cos(angle) * speed)
        vy = int(math.sin(angle) * speed)
        table.append((vx, vy))
    return table


def generate_bullets(n, seed=42):
    """Generate N fake bullets scattered around a point."""
    rng = random.Random(seed)
    bullets = []
    for _ in range(n):
        angle = rng.randint(0, 63)
        raw_x = rng.randint(0, 0x5100)
        raw_y = rng.randint(0, 0x3D00)
        b = FakeBullet(raw_x=raw_x, raw_y=raw_y, angle_index=angle)
        bullets.append(b)
    return bullets


def profile_ai(ai_name, frames=5000, bullets_n=50, progressive=True):
    """Profile the AI decision speed, optionally with progressive frame counts."""
    AI = load_ai(ai_name)
    vel = generate_fake_vel_table()
    ai = AI(vel_table=vel, accel_table=vel)
    bullets = generate_bullets(bullets_n)
    px, py = 150, 60
    logger.info(f"Profiling {ai_name}: {bullets_n} bullets")

    if progressive:
        stages = [100, 200, 500, 1000, 2000, 5000]
        stages = [s for s in stages if s <= frames]
    else:
        stages = [frames]

    for n in stages:
        for _ in range(max(5, n // 20)):  # warmup proportional to size
            ai.decide(px, py, bullets)
        start = time.perf_counter()
        for _ in range(n):
            ai.decide(px, py, bullets)
        elapsed = time.perf_counter() - start
        fps = n / elapsed
        ms = elapsed / n * 1000
        bar = "#" * int(fps / 20)
        print(f"  {n:>5} frames → {elapsed:>6.3f}s  {ms:>6.2f}ms/f  {fps:>6.0f} fps  {bar}")


def profile_cpu(ai_name, frames=500, bullets_n=50):
    """cProfile the AI to find bottlenecks."""
    AI = load_ai(ai_name)
    vel = generate_fake_vel_table()
    ai = AI(vel_table=vel, accel_table=vel)
    bullets = generate_bullets(bullets_n)
    px, py = 150, 60

    pr = cProfile.Profile()
    pr.enable()
    for _ in range(frames):
        ai.decide(px, py, bullets)
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
    ps.print_stats(20)
    print("\n[cProfile — top 20 by cumulative time]")
    print(s.getvalue())


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Profile AI performance")
    p.add_argument("--ai", default="ai_direct", help="AI module name")
    p.add_argument("--frames", type=int, default=5000, help="Frames to simulate")
    p.add_argument("--bullets", type=int, default=50, help="Bullet count")
    p.add_argument("--cpu", action="store_true", help="Also run cProfile")
    args = p.parse_args()

    profile_ai(args.ai, args.frames, args.bullets)
    if args.cpu:
        profile_cpu(args.ai, min(args.frames, 500), args.bullets)
