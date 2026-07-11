"""
ai_basic.py — Inverse-square repulsion field AI.

Each bullet exerts a 1/r² repulsive force away from itself. Sum all force
vectors → wall repulsion (1/d² from each screen edge) → center pull (linear
toward screen center) → net repulsion direction → pick the discrete move
closest to it.

No lookahead, no velocity prediction. Pure reactive force field. O(9+N).
"""
import math

MOVES = [
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


class BasicAI:
    """Inverse-square repulsion with wall avoidance and center pull."""

    EPS = 0.1       # minimum distance to avoid division by zero
    MIN_WALL_DIST = 1.0  # clamp wall distance to prevent force blow-up

    def __init__(self, vel_table=None, accel_table=None,
                 wall_weight=1.0, center_weight=0.00001):
        self.SCREEN_W = 0x130
        self.SCREEN_H = 0xE0
        self.CENTER_X = self.SCREEN_W / 2
        self.CENTER_Y = self.SCREEN_H / 2
        self.wall_weight = wall_weight
        self.center_weight = center_weight

    def decide(self, px, py, bullets):
        fx, fy = 0.0, 0.0

        # 1. Bullet repulsion: F_i = (player - bullet) / r³ → |F| = 1/r²
        for b in bullets:
            dx = px - b.x
            dy = py - b.y
            d2 = dx * dx + dy * dy
            if d2 < self.EPS:
                d2 = self.EPS
            inv_d3 = 1.0 / (d2 * math.sqrt(d2))
            fx += dx * inv_d3
            fy += dy * inv_d3

        # 2. Wall repulsion: 1/d² from each edge, clamping min distance
        dl = max(px, self.MIN_WALL_DIST)
        dr = max(self.SCREEN_W - px, self.MIN_WALL_DIST)
        dt = max(py, self.MIN_WALL_DIST)
        db = max(self.SCREEN_H - py, self.MIN_WALL_DIST)
        fx += self.wall_weight / (dl * dl) - self.wall_weight / (dr * dr)
        fy += self.wall_weight / (dt * dt) - self.wall_weight / (db * db)

        # 3. Center pull: linear force toward screen center
        fx += self.center_weight * (self.CENTER_X - px)
        fy += self.center_weight * (self.CENTER_Y - py)

        # No net force → stay
        if abs(fx) < 1e-9 and abs(fy) < 1e-9:
            return 0

        # Pick discrete move closest to the net force direction
        best_dot = -float('inf')
        best_bits = 0
        for dx, dy, bits in MOVES:
            # Skip moves that go outside screen
            if px + dx < 0 or px + dx >= self.SCREEN_W:
                continue
            if py + dy < 0 or py + dy >= self.SCREEN_H:
                continue
            # Dot product: how aligned is this move with the net force direction?
            if dx == 0 and dy == 0:
                dot = 0.0  # STOP is last resort
            else:
                mag = math.sqrt(dx * dx + dy * dy)
                dot = (dx * fx + dy * fy) / (mag * math.sqrt(fx * fx + fy * fy))
            if dot > best_dot:
                best_dot = dot
                best_bits = bits

        return best_bits
