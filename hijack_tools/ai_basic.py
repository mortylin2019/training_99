"""
ai_basic.py — Inverse-square repulsion field AI.

Each bullet exerts a 1/r² repulsive force away from itself. Sum all force
vectors → net repulsion direction → pick the discrete move closest to it.

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
    """Inverse-square repulsion: sum 1/r² vectors, move with the net force."""

    EPS = 0.1  # minimum distance to avoid division by zero

    def __init__(self, vel_table=None, accel_table=None):
        self.SCREEN_W = 0x130
        self.SCREEN_H = 0xE0

    def decide(self, px, py, bullets):
        if not bullets:
            return 0

        # Sum repulsion vectors: force F_i = (player - bullet) / r³
        # |F_i| = 1/r², direction = unit vector from bullet toward player
        fx, fy = 0.0, 0.0
        for b in bullets:
            dx = px - b.x
            dy = py - b.y
            d2 = dx * dx + dy * dy
            if d2 < self.EPS:
                d2 = self.EPS
            inv_d3 = 1.0 / (d2 * math.sqrt(d2))
            fx += dx * inv_d3
            fy += dy * inv_d3

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
            # Dot product: how aligned is this move with the repulsion direction?
            if dx == 0 and dy == 0:
                dot = 0.0  # STOP is last resort
            else:
                mag = math.sqrt(dx * dx + dy * dy)
                dot = (dx * fx + dy * fy) / (mag * math.sqrt(fx * fx + fy * fy))
            if dot > best_dot:
                best_dot = dot
                best_bits = bits

        return best_bits
