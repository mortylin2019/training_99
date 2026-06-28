"""
ai_direct.py — Pure algorithm: state in → bitmask out.

NO process access, NO memory reading, NO game loop here.
Takes player position + bullets, returns direction bitmask (0–12).

Algorithm: Two-Pass Time-Space Danger Evaluation
  Pass 1 (Immediate): frames 1-5 → panic if collision imminent
  Pass 2 (Strategic): frames 8-50 → center-seeking, open-space
  Uses numpy-vectorized bullet prediction from velocity tables.
"""

import math
import numpy as np


class SuperiorAI:
    """
    Pure decision algorithm — no game I/O.
    
    Usage:
        ai = SuperiorAI(vel_table, accel_table)
        bits = ai.decide(px=150, py=50, bullets=[...])
    """

    MOVE_TABLE = [
        ( 0,  0, 0),   # STOP
        (-1,  0, 1),   # LEFT
        ( 1,  0, 8),   # RIGHT
        ( 0, -1, 2),   # UP
        ( 0,  1, 4),   # DOWN
        (-1, -1, 3),   # UP-LEFT
        (-1,  1, 5),   # DOWN-LEFT
        ( 1, -1, 10),  # UP-RIGHT
        ( 1,  1, 12),  # DOWN-RIGHT
    ]

    def __init__(self, vel_table=None, accel_table=None):
        self.vel_table = vel_table or []
        self.accel_table = accel_table or []

        self.SCREEN_W = 0x130
        self.SCREEN_H = 0xE0
        self.CENTER_X = 0x98
        self.CENTER_Y = 0x2C

        # Hitbox: 2 <= (bx-px) < 13  AND  0 <= (by-py) < 10
        self.HITBOX_X1, self.HITBOX_X2 = 2, 13
        self.HITBOX_Y1, self.HITBOX_Y2 = 0, 10

        self.PREDICT_FRAMES = 60
        self.SPEED = 1

        self.COLLISION = 10_000_000.0
        self.PROXIMITY = 4000.0
        self.CENTER_GRAVITY = 2.0
        self.WALL_FORCE = 3000.0
        self.WALL_MARGIN = 15

    def _velocity(self, angle_idx, btype):
        idx = angle_idx & 0x3F
        if btype == 3 and idx < len(self.accel_table):
            vx, vy = self.accel_table[idx]
        elif idx < len(self.vel_table):
            vx, vy = self.vel_table[idx]
        else:
            return 0.0, 0.0
        return vx / 64.0, vy / 64.0

    def _predict(self, bullets):
        n = len(bullets)
        if n == 0:
            return np.zeros((0, self.PREDICT_FRAMES + 1, 2), dtype=np.float32)
        paths = np.zeros((n, self.PREDICT_FRAMES + 1, 2), dtype=np.float32)
        ts = np.arange(self.PREDICT_FRAMES + 1, dtype=np.float32)
        for i, b in enumerate(bullets):
            vx = b.vx / 64.0 if b.type == 2 else self._velocity(b.angle_index, b.type)[0]
            vy = b.vy / 64.0 if b.type == 2 else self._velocity(b.angle_index, b.type)[1]
            paths[i, :, 0] = float(b.x) + vx * ts
            paths[i, :, 1] = float(b.y) + vy * ts
        return paths

    def _collision(self, px, py, pos):
        if pos.shape[0] == 0:
            return 0, 9999.0
        dx = pos[:, 0] - px
        dy = pos[:, 1] - py
        hits = np.sum((dx >= self.HITBOX_X1) & (dx < self.HITBOX_X2) &
                       (dy >= self.HITBOX_Y1) & (dy < self.HITBOX_Y2))
        cx, cy = px + 7.5, py + 5.0
        dists = np.sqrt((pos[:, 0] - cx) ** 2 + (pos[:, 1] - cy) ** 2)
        return int(hits), float(np.min(dists))

    def _score(self, px, py, paths, f):
        if f >= paths.shape[1]:
            f = paths.shape[1] - 1
        hits, md = self._collision(px, py, paths[:, f, :])
        if hits > 0:
            return self.COLLISION + hits, True
        d = self.PROXIMITY / max(md * md, 1.0)
        d += math.hypot(px - self.CENTER_X, py - self.CENTER_Y) * self.CENTER_GRAVITY
        if px < self.WALL_MARGIN: d += (self.WALL_MARGIN - px) * self.WALL_FORCE
        elif px > self.SCREEN_W - self.WALL_MARGIN: d += (px - (self.SCREEN_W - self.WALL_MARGIN)) * self.WALL_FORCE
        if py < self.WALL_MARGIN: d += (self.WALL_MARGIN - py) * self.WALL_FORCE
        elif py > self.SCREEN_H - self.WALL_MARGIN: d += (py - (self.SCREEN_H - self.WALL_MARGIN)) * self.WALL_FORCE
        return d, False

    def _eval(self, px, py, dx, dy, paths):
        s, fatal = 0.0, False
        for f in [1, 2, 3, 4, 5]:
            fx = max(0, min(self.SCREEN_W, px + dx * self.SPEED * f))
            fy = max(0, min(self.SCREEN_H, py + dy * self.SPEED * f))
            v, hit = self._score(fx, fy, paths, f)
            s += v / (f * 0.3 + 0.3)
            if hit: fatal = True
        if not fatal:
            for f in [8, 12, 18, 25, 35, 50]:
                fx = max(0, min(self.SCREEN_W, px + dx * self.SPEED * f))
                fy = max(0, min(self.SCREEN_H, py + dy * self.SPEED * f))
                v, _ = self._score(fx, fy, paths, f)
                s += v / (1.0 + f * 0.06)
        return s, fatal

    # ── Public API ─────────────────────────────────────────────────

    def decide(self, px, py, bullets):
        """
        Decide best input bitmask for this frame.
        
        Args:
            px, py: player pixel coordinates
            bullets: list of Bullet objects (only active, angle_index != 0xFF)
        
        Returns:
            int: bitmask (0–12) for G_InputState
        """
        if not bullets:
            return 0
        if px <= 0 or py <= 0:
            px, py = self.CENTER_X, self.CENTER_Y

        paths = self._predict(bullets)
        best_score, best_bits = float('inf'), 0

        for dx, dy, bits in self.MOVE_TABLE:
            score, _ = self._eval(px, py, dx, dy, paths)
            if score < best_score:
                best_score, best_bits = score, bits

        return best_bits
