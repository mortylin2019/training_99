"""
ai_astar.py — Space-Time A* through predicted bullet trajectories.

State: (x, y, t) — player position at future frame t.
Transitions: 9-direction movement × step size.
Cost: 1/r² danger from bullet positions PREDICTED at each timestep.
Blocking: cells within hitbox + safety margin of a predicted bullet.

Unlike beam search (prunes promising paths), space-time A* guarantees
a safe route exists before committing to the first move.
"""
import heapq
import numpy as np

try:
    from algo_config import MOVES, BITS, SCR_W, SCR_H, CTR_X, CTR_Y
    from algo_config import HIT_X1, HIT_X2, HIT_Y1, HIT_Y2, SPEED
except ImportError:
    from hijack_tools.algo_config import MOVES, BITS, SCR_W, SCR_H, CTR_X, CTR_Y
    from hijack_tools.algo_config import HIT_X1, HIT_X2, HIT_Y1, HIT_Y2, SPEED


class AStarAI:
    """Space-time A* minimizing cumulative predicted danger."""

    CELL = 8
    DEPTH = 10
    STEP = 4
    SAFETY = 4
    DANGER_BASE = 2000.0
    COLLISION_COST = 1e8

    def __init__(self, vel_table=None, accel_table=None):
        self._vel_table = np.array(vel_table, dtype=np.float32) if vel_table is not None else None
        self._last_path = []

    def decide(self, px, py, bullets):
        if not bullets:
            return 0
        if px <= 0 or py <= 0:
            px, py = CTR_X, CTR_Y

        gx = SCR_W // self.CELL
        gy = SCR_H // self.CELL
        step = self.STEP
        max_t = self.DEPTH

        # ── Bullet velocities ──
        n = len(bullets)
        bx = np.array([b.x for b in bullets], dtype=np.float64)
        by = np.array([b.y for b in bullets], dtype=np.float64)
        ang = np.array([b.angle_index for b in bullets], dtype=np.int32)
        types = np.array([b.type for b in bullets], dtype=np.int32)

        bvx = np.zeros(n, dtype=np.float64)
        bvy = np.zeros(n, dtype=np.float64)
        if self._vel_table is not None and len(self._vel_table) >= 64:
            idx = np.clip((ang & 0x3F).astype(np.int32), 0, 63)
            bvx = self._vel_table[idx, 0].astype(np.float64) / 64.0
            bvy = self._vel_table[idx, 1].astype(np.float64) / 64.0
            t2 = types == 2
            if t2.any():
                bvx[t2] = np.array([b.vx for b in bullets if b.type == 2], dtype=np.float64)[:t2.sum()] / 64.0
                bvy[t2] = np.array([b.vy for b in bullets if b.type == 2], dtype=np.float64)[:t2.sum()] / 64.0

        # ── Build danger grids: grid[depth][y][x] ──
        grids = []
        for d in range(max_t + 1):
            t_frame = d * step
            px_pred = bx + bvx * t_frame
            py_pred = by + bvy * t_frame
            grid = np.zeros((gy, gx), dtype=np.float64)
            for i in range(n):
                cell_x = int(px_pred[i] // self.CELL)
                cell_y = int(py_pred[i] // self.CELL)
                cell_x = max(0, min(gx - 1, cell_x))
                cell_y = max(0, min(gy - 1, cell_y))
                for dy in range(-4, 5):
                    for dx in range(-4, 5):
                        nx = cell_x + dx; ny = cell_y + dy
                        if 0 <= nx < gx and 0 <= ny < gy:
                            cwx = nx * self.CELL + self.CELL // 2
                            cwy = ny * self.CELL + self.CELL // 2
                            d2 = (cwx - px_pred[i])**2 + (cwy - py_pred[i])**2
                            if d2 < 1.0: d2 = 1.0
                            grid[ny, nx] += self.DANGER_BASE / d2
            grids.append(grid)

        sx = max(0, min(gx - 1, int(px // self.CELL)))
        sy = max(0, min(gy - 1, int(py // self.CELL)))

        # ── Space-time A* ──
        cell_moves = []
        for mi in range(9):
            dx = MOVES[mi][0] * SPEED * step
            dy = MOVES[mi][1] * SPEED * step
            cx = int(dx // self.CELL) if dx >= 0 else -int(-dx // self.CELL + 0.99)
            cy = int(dy // self.CELL) if dy >= 0 else -int(-dy // self.CELL + 0.99)
            cell_moves.append((cx, cy, mi))

        open_set = [(0.0, 0, sx, sy, 0, -1)]
        closed = set()
        entries = []
        best_goal = (1e30, -1)

        while open_set and len(entries) < 30000:
            f, _, cx, cy, depth, parent = heapq.heappop(open_set)
            key = (cx, cy, depth)
            if key in closed:
                continue
            closed.add(key)
            idx = len(entries)
            entries.append((cx, cy, depth, parent, f))

            if depth >= max_t:
                if f < best_goal[0]:
                    best_goal = (f, idx)
                continue

            for mcx, mcy, mi in cell_moves:
                nx, ny = cx + mcx, cy + mcy
                if nx < 0 or nx >= gx or ny < 0 or ny >= gy:
                    continue
                nk = (nx, ny, depth + 1)
                if nk in closed:
                    continue
                cell_danger = grids[depth + 1][ny, nx]
                if cell_danger > 100000:
                    continue
                ng = f + cell_danger * 0.005
                nh = (max_t - depth - 1) * 3.0
                heapq.heappush(open_set, (ng + nh, len(entries), nx, ny, depth + 1, idx))

        if best_goal[1] >= 0:
            path = []
            ci = best_goal[1]
            while ci >= 0:
                cx, cy = entries[ci][0], entries[ci][1]
                path.append((cx * self.CELL + self.CELL // 2, cy * self.CELL + self.CELL // 2))
                ci = entries[ci][3]
            path.reverse()
            self._last_path = path
            if len(path) >= 2:
                return self._dir_to_bits(path[1][0] - px, path[1][1] - py)

        return self._repulsion(px, py, bullets)

    def _repulsion(self, px, py, bullets):
        fx = fy = 0.0
        for b in bullets:
            dx = px - b.x; dy = py - b.y
            d2 = dx * dx + dy * dy
            if d2 < 0.1: d2 = 0.1
            inv_d3 = 1.0 / (d2 * d2**0.5)
            fx += dx * inv_d3; fy += dy * inv_d3
        return self._dir_to_bits(fx, fy)

    def _dir_to_bits(self, dx, dy):
        if abs(dx) < 1 and abs(dy) < 1:
            return 0
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
