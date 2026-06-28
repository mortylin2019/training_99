"""
simulator.py - Faithful 99.exe simulator for fast AI testing.

All mechanics from decompiled code: 4 bullet types, 7 patterns,
exact hitbox, graze system. Per-instance RNG, ProcessPool for scale.
"""

import math
import time
import random
import os
import sys
import numpy as np
from dataclasses import dataclass
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="SUCCESS")

# -- Constants --
SCR_W, SCR_H = 0x130, 0xE0
RAW_MAX_X, RAW_MAX_Y = 0x5100, 0x3D00
DIFF_BULLETS = {0: 30, 1: 50, 2: 100, 3: 200}
PATTERN_TABLE = {
    0: {"type": 0, "timer": 0}, 1: {"type": 0, "timer": 0},
    2: {"type": 1, "timer": 0x30}, 3: {"type": 1, "timer": 0x20},
    4: {"type": 1, "timer": 0x10}, 5: {"type": 1, "timer": 0},
    6: {"type": 3, "timer": 0}, 7: {"type": 2, "timer": 0},
}


class LCG:
    def __init__(self, seed=0):
        self.state = seed & 0xFFFFFFFF
    def next(self):
        self.state = (self.state * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        return (self.state >> 16) & 0x7FFF


@dataclass
class SimBullet:
    raw_x: int = 0; raw_y: int = 0; angle_index: int = 0
    active: int = 1; type: int = 0; timer: int = 0
    counter: int = 0; grazed: int = 0; idx: int = 0
    vx: int = 0; vy: int = 0

    @property
    def x(self): return (self.raw_x >> 6) - 4
    @property
    def y(self): return (self.raw_y >> 6) - 4


class GameSimulator:
    def __init__(self, difficulty=1, seed=None, vel_table=None, accel_table=None):
        self.rng = LCG(seed if seed is not None else random.randint(0, 0x7FFFFFFF))
        self.difficulty = difficulty
        self.start_bullets = DIFF_BULLETS.get(difficulty, 50)
        self.vel_table = vel_table or [(0, 0)] * 64
        self.accel_table = accel_table or [(0, 0)] * 64
        self.reset()

    def reset(self):
        self.px, self.py = 0x98, 0x2C
        self.frame = 0
        self.dead = False
        self.bullet_count = self.start_bullets
        self.next_spawn = 3000
        self.next_pattern = 5000
        self.pattern = 0
        self.pattern_duration = 0
        self.bounce_limit = 0
        self.active_near = 0
        self.graze_total = 0
        self.graze_chain = 0
        self._graze_timer = 0
        self.bullets = []
        for _ in range(self.start_bullets):
            self._spawn_bullet()

    def _spawn_bullet(self):
        b = SimBullet()
        edge = self.rng.next() & 3
        if edge == 0:    b.raw_x, b.raw_y = self.rng.next() % RAW_MAX_X, 0
        elif edge == 1:  b.raw_x, b.raw_y = self.rng.next() % RAW_MAX_X, RAW_MAX_Y
        elif edge == 2:  b.raw_x, b.raw_y = 0, self.rng.next() % RAW_MAX_Y
        else:            b.raw_x, b.raw_y = RAW_MAX_X, self.rng.next() % RAW_MAX_Y
        pat = self.pattern
        info = PATTERN_TABLE.get(pat, PATTERN_TABLE[0])
        b.type = info["type"]; b.timer = info["timer"]
        b.counter = 0; b.grazed = 0; b.vx = 0; b.vy = 0
        if pat == 5: b.timer = ((self.rng.next() & 3) + 1) * 16
        if pat == 7:
            if self.bounce_limit >= 4: b.type = 0
            else: self.bounce_limit += 1; b.type = 2
        b.angle_index = self.rng.next() & 0x3F
        self.bullets.append(b)
        self.bullet_count += 1

    def _move_bullet(self, b):
        if b.type == 1:
            b.counter += 1
            if b.counter >= b.timer:
                b.counter = 0
                bpx, bpy = b.x, b.y
                ang = math.atan2(self.py - bpy, self.px - bpx)
                target = int((ang / (2 * math.pi)) * 64 + 32) & 0x3F
                cur = b.angle_index
                if target != cur:
                    if target < cur: cur = (cur - 0x40) & 0xFF
                    diff = (target - cur) & 0xFF
                    if diff < 0x19: b.angle_index = (b.angle_index + 1) & 0x3F
                    elif diff < 0x28: b.type = 0
                    else: b.angle_index = (b.angle_index - 1) & 0x3F
            idx = b.angle_index & 0x3F
            vx, vy = self.vel_table[idx]
            b.raw_x += vx; b.raw_y += vy
        elif b.type == 2:
            tx, ty = self.px + 6, self.py + 6
            bpx, bpy = b.x, b.y
            if bpx < tx and b.vx < 96: b.vx += 1
            elif bpx >= tx and b.vx > -96: b.vx -= 1
            if bpy < ty and b.vy < 96: b.vy += 1
            elif bpy >= ty and b.vy > -96: b.vy -= 1
            b.raw_x += b.vx; b.raw_y += b.vy
        elif b.type == 3:
            idx = b.angle_index & 0x3F
            vx, vy = self.accel_table[idx]
            b.raw_x += vx; b.raw_y += vy
        else:
            idx = b.angle_index & 0x3F
            vx, vy = self.vel_table[idx]
            b.raw_x += vx; b.raw_y += vy

    def step(self, input_bits):
        if self.dead: return False, []
        self.frame += 1
        dx = (1 if (input_bits & 8) else 0) - (1 if (input_bits & 1) else 0)
        dy = (1 if (input_bits & 4) else 0) - (1 if (input_bits & 2) else 0)
        self.px = max(0, min(SCR_W, self.px + dx))
        self.py = max(0, min(SCR_H, self.py + dy))
        active = []
        for b in self.bullets:
            if b.angle_index == 0xFF: continue
            self._move_bullet(b)
            if b.raw_x >= RAW_MAX_X or b.raw_y >= RAW_MAX_Y:
                if b.type == 2: self.bounce_limit = max(0, self.bounce_limit - 1)
                self._recycle(b); continue
            bpx, bpy = b.x, b.y
            dx_b, dy_b = bpx - self.px, bpy - self.py
            if dx_b + 4 < 23 and dy_b + 6 < 14:
                if not b.grazed: b.grazed = 1; self.active_near += 1
            elif b.grazed:
                b.grazed = 0; self.active_near -= 1
                if self.active_near > 0:
                    self.graze_total += self.active_near
                    if self.frame < self._graze_timer + 1000:
                        if self.graze_chain < 10: self.graze_chain += 1
                    else: self.graze_chain = 1
                    self._graze_timer = self.frame
            if 2 <= dx_b < 13 and 0 <= dy_b < 10: self.dead = True
            if not self.dead: active.append(b)
        if self.bullet_count < 299 and self.frame > self.next_spawn and self.pattern != 7:
            self._spawn_bullet(); self.next_spawn = self.frame + 3000
        if self.frame > self.next_pattern:
            if self.pattern == 0:
                if self.rng.next() < 0x3000:
                    self.pattern = (self.rng.next() % 7) + 1
                    self.pattern_duration = 100; self.next_pattern = self.frame + 10000
                else: self.next_pattern = self.frame + 5000
            else:
                self.pattern_duration -= 1
                if self.pattern_duration <= 0:
                    self.pattern = 0; self.next_pattern = self.frame + 5000
        return not self.dead, active

    def _recycle(self, b):
        edge = self.rng.next() & 3
        if edge == 0:    b.raw_x, b.raw_y = self.rng.next() % RAW_MAX_X, 0
        elif edge == 1:  b.raw_x, b.raw_y = self.rng.next() % RAW_MAX_X, RAW_MAX_Y
        elif edge == 2:  b.raw_x, b.raw_y = 0, self.rng.next() % RAW_MAX_Y
        else:            b.raw_x, b.raw_y = RAW_MAX_X, self.rng.next() % RAW_MAX_Y
        b.angle_index = self.rng.next() & 0x3F
        b.type = 0; b.counter = 0; b.grazed = 0; b.vx = 0; b.vy = 0

    def get_visible_bullets(self):
        return [b for b in self.bullets if b.angle_index != 0xFF]


# -- AI loader --
def _load_ai(name):
    if name == "ai_beam":
        try: from ai_beam import BeamAI
        except ImportError: from hijack_tools.ai_beam import BeamAI
        return BeamAI
    if name == "ai_direct":
        try: from ai_direct import SuperiorAI
        except ImportError: from hijack_tools.ai_direct import SuperiorAI
        return SuperiorAI
    raise ValueError(f"Unknown AI: {name}")


def _run_one(args):
    ai_name, difficulty, max_frames, seed, vel, accel = args
    AI = _load_ai(ai_name)
    ai = AI(vel_table=vel, accel_table=accel)
    sim = GameSimulator(difficulty=difficulty, seed=seed, vel_table=vel, accel_table=accel)
    fake = [SimBullet(raw_x=0x8000, raw_y=0x4000, angle_index=i) for i in range(20)]
    for _ in range(3): ai.decide(152, 44, fake)
    for _ in range(max_frames):
        bits = ai.decide(sim.px, sim.py, sim.get_visible_bullets())
        alive, _ = sim.step(bits)
        if not alive: return sim.frame
    return max_frames


def main():
    import argparse
    from concurrent.futures import ProcessPoolExecutor
    try:
        from tqdm import tqdm; has_tqdm = True
    except ImportError:
        has_tqdm = False
        def tqdm(x, **kw): return x

    p = argparse.ArgumentParser()
    p.add_argument("--ai", default="ai_beam")
    p.add_argument("--runs", type=int, default=500)
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=30000)
    p.add_argument("-j", "--workers", type=int, default=0)
    args = p.parse_args()

    vel = []; accel = []
    for i in range(64):
        a = i * 2 * math.pi / 64; s = 160
        vel.append((int(math.cos(a) * s), int(math.sin(a) * s)))
        accel.append((int(math.cos(a) * s * 1.5), int(math.sin(a) * s * 1.5)))

    workers = args.workers or os.cpu_count() or 4
    logger.info(f"Sim: {args.runs}x{args.ai} diff{args.difficulty} | {workers} procs")
    tasks = [(args.ai, args.difficulty, args.max_frames, i * 12345, vel, accel)
             for i in range(args.runs)]
    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        if has_tqdm:
            with tqdm(total=args.runs, desc="Simulating", unit="run") as pb:
                for f in pool.map(_run_one, tasks): results.append(f); pb.update(1)
        else:
            for i, f in enumerate(pool.map(_run_one, tasks)):
                results.append(f)
                if (i + 1) % max(1, args.runs // 10) == 0:
                    logger.info(f"  {i+1}/{args.runs}")

    elapsed = time.time() - t0
    times = [f / 80.0 for f in results]
    st = sorted(times); n = len(st)
    print(f"\n{'='*60}\n  SIM: {n} runs, {args.ai}, {elapsed:.0f}s "
          f"({n/elapsed:.0f} run/s, {sum(results)/elapsed:.0f} fps)")
    print(f"  Best:{max(times):.1f}s Worst:{min(times):.1f}s "
          f"Avg:{sum(times)/n:.1f}s Med:{st[n//2]:.1f}s")
    print(f"  P90:{st[int(n*.9)]:.1f}s P75:{st[int(n*.75)]:.1f}s P25:{st[int(n*.25)]:.1f}s")
    buckets = [0, 3, 5, 10, 15, 20, 30, 45, 60, 90, 999]
    print("  Histogram:")
    for i in range(len(buckets) - 1):
        c = sum(1 for t in times if buckets[i] <= t < buckets[i+1])
        print(f"    {buckets[i]:>3}-{buckets[i+1]:<3}s: {c:>4} {'#' * (c * 40 // max(n, 1))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
