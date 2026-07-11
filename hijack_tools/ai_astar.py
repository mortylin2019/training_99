"""
ai_astar.py — BFS Space-Time search with safety margin.

JIT danger grids + BFS layer-by-layer exploration through time.
No priority queue, no heuristic — explores ALL reachable cells
at each depth step, picks the path ending at lowest danger.

Safety margin: cells with danger > THRESHOLD are blocked.
Center pull: targets cells near screen center at max depth.
"""
import numpy as np
from collections import deque

try:
    from algo_config import MOVES, BITS, SCR_W, SCR_H, SPEED
except ImportError:
    from hijack_tools.algo_config import MOVES, BITS, SCR_W, SCR_H, SPEED

CELL = 4; GX = SCR_W // CELL; GY = SCR_H // CELL
DEPTH = 16; STEP = 4; DANGER_BASE = 2000.0
BLOCK_THRESHOLD = 5000.0  # cells above this = blocked (safety margin)

MOVE_DX = np.zeros(9, dtype=np.int32); MOVE_DY = np.zeros(9, dtype=np.int32)
for mi in range(9):
    dx = MOVES[mi][0] * SPEED * STEP; dy = MOVES[mi][1] * SPEED * STEP
    MOVE_DX[mi] = int(dx // CELL) if dx >= 0 else -int((-dx) // CELL + 0.99)
    MOVE_DY[mi] = int(dy // CELL) if dy >= 0 else -int((-dy) // CELL + 0.99)

from numba import njit

@njit
def build_grid(pred_x, pred_y, gx, gy, cell):
    n = len(pred_x); grid = np.zeros((gy, gx), dtype=np.float32)
    for i in range(n):
        bx, by = pred_x[i], pred_y[i]
        cx = max(0, min(gx - 1, int(bx // cell)))
        cy = max(0, min(gy - 1, int(by // cell)))
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                nx, ny = cx + dx, cy + dy
                if nx < 0 or nx >= gx or ny < 0 or ny >= gy: continue
                d2 = (nx*cell+cell//2 - bx)**2 + (ny*cell+cell//2 - by)**2
                if d2 < 4.0: d2 = 4.0
                grid[ny, nx] += DANGER_BASE / d2
    return grid


def bfs_search(grids, sx, sy, gx, gy, max_d):
    """BFS through space-time grid. Returns (found, first_move_idx).
    
    Explores all reachable cells layer by layer. Each cell stores
    parent info for path reconstruction. At max depth, picks the
    cell with lowest danger (preferring center).
    """
    # visited[depth][y][x] = (from_cx, from_cy, from_depth, move_idx)
    visited = [[[None for _ in range(gx)] for _ in range(gy)] for _ in range(max_d + 1)]
    
    # Queue: (cx, cy, depth)
    q = deque()
    q.append((sx, sy, 0))
    visited[0][sy][sx] = (-1, -1, -1, -1)  # root marker
    
    # Best goal: (danger_score, cx, cy) — lower is better
    best = (1e30, -1, -1, -1)  # danger, cx, cy, move_idx
    
    while q:
        cx, cy, d = q.popleft()
        nd = d + 1
        
        if nd > max_d:
            # Reached max depth — check if this is the best goal
            danger = float(grids[d][cy][cx])
            # Prefer center: mild pull toward center cells
            center_bonus = abs(cx - gx//2) * 0.5 + abs(cy - gy//2) * 0.5
            score = danger + center_bonus
            if score < best[0]:
                best = (score, cx, cy, d)
            continue
        
        # Expand 9 moves at next depth
        for mi in range(9):
            nx, ny = cx + MOVE_DX[mi], cy + MOVE_DY[mi]
            if nx < 0 or nx >= gx or ny < 0 or ny >= gy:
                continue
            if visited[nd][ny][nx] is not None:
                continue
            
            # Safety check: block cells with danger above threshold
            cell_danger = float(grids[nd][ny][nx])
            if cell_danger > BLOCK_THRESHOLD:
                continue
            
            visited[nd][ny][nx] = (cx, cy, d, mi)
            q.append((nx, ny, nd))
    
    # No path found to max depth — find longest reachable depth
    if best[2] < 0:
        for d in range(max_d, 0, -1):
            for cy in range(gy):
                for cx in range(gx):
                    if visited[d][cy][cx] is not None:
                        danger = float(grids[d][cy][cx])
                        if danger < best[0]:
                            best = (danger, cx, cy, d)
            if best[2] >= 0:
                break
    
    if best[2] < 0:
        return False, 0
    
    # Trace path back to find first move
    bcx, bcy, bd = best[1], best[2], best[3]
    while bd > 1 and visited[bd][bcy][bcx] is not None:
        pcx, pcy, pd, mi = visited[bd][bcy][bcx]
        if pd == 0:  # Found the move from root
            return True, mi
        bcx, bcy, bd = pcx, pcy, pd
    
    return False, 0


class AStarAI:
    def __init__(self, vel_table=None, accel_table=None):
        self._vt = np.array(vel_table, dtype=np.float32) if vel_table is not None else None
    
    def decide(self, px, py, bullets):
        if not bullets: return 0
        if px <= 0 or py <= 0: px, py = 152, 112
        
        n = len(bullets)
        bx = np.array([b.x for b in bullets], dtype=np.float64)
        by = np.array([b.y for b in bullets], dtype=np.float64)
        ang = np.array([b.angle_index for b in bullets], dtype=np.int32)
        types = np.array([b.type for b in bullets], dtype=np.int32)
        
        bvx = np.zeros(n, dtype=np.float64); bvy = np.zeros(n, dtype=np.float64)
        if self._vt is not None and len(self._vt) >= 64:
            idx = np.clip((ang & 0x3F).astype(np.int32), 0, 63)
            bvx[:] = self._vt[idx, 0] / 64.0; bvy[:] = self._vt[idx, 1] / 64.0
            t2 = types == 2
            if t2.any():
                t2i = np.where(t2)[0]
                t2b = [bullets[i] for i in t2i]
                bvx[t2] = np.array([b.vx for b in t2b], dtype=np.float64) / 64.0
                bvy[t2] = np.array([b.vy for b in t2b], dtype=np.float64) / 64.0
        
        grids = []
        for d in range(DEPTH + 1):
            tf = d * STEP
            grids.append(build_grid(bx + bvx * tf, by + bvy * tf, GX, GY, CELL))
        
        sx = max(0, min(GX - 1, int(px // CELL)))
        sy = max(0, min(GY - 1, int(py // CELL)))
        f, m = bfs_search(grids, sx, sy, GX, GY, DEPTH)
        if f: return int(BITS[m])
        
        # Repulsion fallback
        fx, fy = 0.0, 0.0
        for i in range(len(bx)):
            dx = px - bx[i]; dy = py - by[i]
            d2 = dx*dx + dy*dy
            if d2 < 0.1: d2 = 0.1
            inv = 1.0 / (d2 * d2**0.5)
            fx += dx * inv; fy += dy * inv
        bd, bb = -float('inf'), 0
        for mi in range(9):
            mdx, mdy = MOVES[mi]
            if mdx == 0 and mdy == 0: dot = -0.1
            else:
                mm = (mdx*mdx + mdy*mdy)**0.5
                vm = max(abs(fx)+abs(fy), 0.001)
                dot = (mdx*fx + mdy*fy) / (mm * vm)
            if dot > bd: bd, bb = dot, BITS[mi]
        return bb
