"""
ai_astar.py — A* pathfinding through bullet danger field.

Unlike beam search (which optimizes danger at waypoints), A* finds a
complete clear path through the bullet field with a safety margin.
Bullets create "blocked zones" — A* routes around them.

Key insight: "dying in low density" happens because beam search takes
small risks that accumulate. A* with safety margin refuses ANY plan
that passes too close to a bullet — it finds a new route entirely.

Grid: 2×2 px cells (152×112 grid). Each cell is blocked if any bullet
is within hitbox + safety margin. A* finds the shortest clear path to
the cell with the lowest bullet density.
"""
import heapq
import numpy as np

from algo_config import (
    MOVES, BITS, SCR_W, SCR_H, CTR_X, CTR_Y,
    HIT_X1, HIT_X2, HIT_Y1, HIT_Y2,
    SAFETY_MARGIN, WALL_MARGIN,
)
try:
    from algo_config import SAFETY_MARGIN
except ImportError:
    SAFETY_MARGIN = 2.0


class AStarAI:
    """A* pathfinding with bullet-avoidance safety margin.

    Builds a danger grid from bullet positions. A* finds the shortest
    clear path to the safest area. Moves one step per frame, replans.
    """

    CELL = 4           # px per grid cell
    SAFETY = 4          # px — extra clearance beyond hitbox (softer: cost, not block)
    DANGER_BASE = 2000.0

    def __init__(self, vel_table=None, accel_table=None):
        self._last_path = []
        self._last_target = None

    def decide(self, px, py, bullets):
        if not bullets:
            return 0

        gx = SCR_W // self.CELL
        gy = SCR_H // self.CELL

        # ── Build danger grid (continuous, not binary) ──
        danger = np.zeros((gy, gx), dtype=np.float32)
        for b in bullets:
            cx = max(0, min(gx - 1, int(b.x) // self.CELL))
            cy = max(0, min(gy - 1, int(b.y) // self.CELL))
            # 1/r² danger from bullet to cell center
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < gx and 0 <= ny < gy:
                        cell_x = nx * self.CELL + self.CELL // 2
                        cell_y = ny * self.CELL + self.CELL // 2
                        d2 = (cell_x - b.x)**2 + (cell_y - b.y)**2
                        if d2 < 1.0: d2 = 1.0
                        danger[ny, nx] += self.DANGER_BASE / d2

        # Player cell
        sx = max(0, min(gx - 1, px // self.CELL))
        sy = max(0, min(gy - 1, py // self.CELL))

        # ── Find target: unblocked cell with lowest danger ──
        best_score = 1e9
        tx, ty = gx // 2, gy // 2  # default: center
        for cy in range(gy):
            for cx in range(gx):
                score = danger[cy, cx] + abs(cx - gx // 2) * 0.5 + abs(cy - gy // 2) * 0.5
                if score < best_score:
                    best_score = score
                    tx, ty = cx, cy

        # ── Weighted A*: minimize cumulative danger, not distance ──
        path = self._astar_danger(sx, sy, tx, ty, danger, gx, gy)
        if not path or len(path) < 2:
            return self._repulsion_move(px, py, bullets)

        self._last_path = [(cx * self.CELL + self.CELL // 2,
                            cy * self.CELL + self.CELL // 2) for cx, cy in path]
        self._last_target = (tx * self.CELL, ty * self.CELL)

        next_cell = path[1] if len(path) > 1 else path[0]
        nx = next_cell[0] * self.CELL + self.CELL // 2
        ny = next_cell[1] * self.CELL + self.CELL // 2
        return self._dir_to_bits(nx - px, ny - py)

    def _astar_danger(self, sx, sy, tx, ty, danger, gx, gy):
        """Weighted A* minimizing cumulative danger (not distance)."""
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (-1, -1), (1, -1), (-1, 1)]

        open_set = [(0.0, 0, sx, sy)]
        came_from = {}
        g_score = {(sx, sy): 0.0}

        while open_set:
            f, g, cx, cy = heapq.heappop(open_set)

            if (cx, cy) == (tx, ty):
                path = [(tx, ty)]
                while (cx, cy) in came_from:
                    cx, cy = came_from[(cx, cy)]
                    path.append((cx, cy))
                path.reverse()
                return path

            for dx, dy in dirs:
                nx, ny = cx + dx, cy + dy
                if nx < 0 or nx >= gx or ny < 0 or ny >= gy:
                    continue

                # Cost = danger at target cell (how dangerous is this step?)
                step_cost = danger[ny, nx] * 0.01  # scale danger to reasonable cost
                ng = g + step_cost
                if ng < g_score.get((nx, ny), 1e9):
                    g_score[(nx, ny)] = ng
                    nh = abs(nx - tx) + abs(ny - ty)
                    heapq.heappush(open_set, (ng + nh + danger[ny, nx] * 0.01, id((nx, ny)), nx, ny))
                    came_from[(nx, ny)] = (cx, cy)
        return None

    def _repulsion_move(self, px, py, bullets):
        """Fallback: 1/r² repulsion when no clear path exists."""
        fx, fy = 0.0, 0.0
        for b in bullets:
            dx = px - b.x; dy = py - b.y
            d2 = dx * dx + dy * dy
            if d2 < 0.1: d2 = 0.1
            inv_d3 = 1.0 / (d2 * d2**0.5)
            fx += dx * inv_d3; fy += dy * inv_d3
        best_dot = -float('inf')
        best_bits = 0
        for mi in range(9):
            mdx, mdy = MOVES[mi]
            if mdx == 0 and mdy == 0:
                dot = -0.1
            else:
                mmag = (mdx * mdx + mdy * mdy)**0.5
                vmag = max(abs(fx) + abs(fy), 0.001)
                dot = (mdx * fx + mdy * fy) / (mmag * vmag)
            if dot > best_dot:
                best_dot, best_bits = dot, BITS[mi]
        return best_bits

    def _dir_to_bits(self, dx, dy):
        """Convert (dx, dy) to closest discrete BITS value."""
        if abs(dx) < 1 and abs(dy) < 1:
            return 0  # STOP
        best_dot = -float('inf')
        best_bits = 0
        for mi in range(9):
            mdx, mdy = MOVES[mi]
            if mdx == 0 and mdy == 0:
                dot = -0.1
            else:
                mmag = (mdx * mdx + mdy * mdy)**0.5
                vmag = max(abs(dx) + abs(dy), 0.001)
                dot = (mdx * dx + mdy * dy) / (mmag * vmag)
            if dot > best_dot:
                best_dot, best_bits = dot, BITS[mi]
        return best_bits
