"""
ai_astar.py — Grid-Beam Search: beam search on JIT danger grid.

Key insight: BFS explored ALL ~3000 cells/depth. Beam search explores
only K cells. Do beam search ON the grid — JIT danger lookup + top-K pruning.

Combines: JIT grid speed (0.1ms) + beam pruning (450 candidates/depth).
"""
import numpy as np
from numba import njit

try:
    from algo_config import MOVES, BITS, SCR_W, SCR_H, SPEED
except ImportError:
    from hijack_tools.algo_config import MOVES, BITS, SCR_W, SCR_H, SPEED

CELL = 3; GX = SCR_W // CELL; GY = SCR_H // CELL  # 101×74 grid
DEPTH = 20; STEP = 4; DANGER_BASE = 2000.0
BEAM_K = 30  # top-K cells per depth (was 50 in pixel beam)

MOVE_DX = np.zeros(9, dtype=np.int32); MOVE_DY = np.zeros(9, dtype=np.int32)
for mi in range(9):
    dx = MOVES[mi][0] * SPEED * STEP; dy = MOVES[mi][1] * SPEED * STEP
    MOVE_DX[mi] = int(dx / CELL) if dx >= 0 else -int((-dx) / CELL + 0.99)
    MOVE_DY[mi] = int(dy / CELL) if dy >= 0 else -int((-dy) / CELL + 0.99)
BITS_ARR = np.array(BITS, dtype=np.int32)

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

@njit
def beam_on_grid(grids, sx, sy, gx, gy, max_d, K):
    """Beam search on precomputed danger grids.
    
    Like pixel beam search but uses grid cells instead of continuous positions.
    Keeps top-K cells per depth by cumulative danger.
    Returns best first-move index.
    """
    # Beam state: (cx, cy, first_move, cumulative_danger)
    b_cx = np.zeros(K, dtype=np.int32)
    b_cy = np.zeros(K, dtype=np.int32)
    b_fm = np.full(K, -1, dtype=np.int32)
    b_sc = np.full(K, 1e30, dtype=np.float64)
    b_cx[0] = sx; b_cy[0] = sy; b_fm[0] = -1; b_sc[0] = 0.0
    b_cnt = 1
    
    cand_cx = np.zeros(K * 9, dtype=np.int32)
    cand_cy = np.zeros(K * 9, dtype=np.int32)
    cand_fm = np.zeros(K * 9, dtype=np.int32)
    cand_sc = np.full(K * 9, 1e30, dtype=np.float64)
    
    for d in range(max_d):
        nd = d + 1
        ci = 0
        
        for bi in range(b_cnt):
            for mi in range(9):
                nx = b_cx[bi] + MOVE_DX[mi]
                ny = b_cy[bi] + MOVE_DY[mi]
                if nx < 0 or nx >= gx or ny < 0 or ny >= gy:
                    continue
                
                danger = float(grids[nd][ny][nx])
                if danger > 50000:  # blocked
                    continue
                
                # Cumulative danger (1/r² weighted by depth)
                w = 1.0 / (0.5 + (nd * STEP) * 0.03)
                total = b_sc[bi] + danger * w
                
                cand_cx[ci] = nx; cand_cy[ci] = ny
                cand_fm[ci] = b_fm[bi] if b_fm[bi] >= 0 else mi
                cand_sc[ci] = total
                ci += 1
        
        # Top-K selection (insertion sort)
        for k in range(K):
            b_cx[k] = -1; b_sc[k] = 1e30
        b_cnt = 0
        for i in range(ci):
            score = cand_sc[i]
            for k in range(K):
                if score < b_sc[k]:
                    for j in range(K - 1, k, -1):
                        b_cx[j] = b_cx[j-1]; b_cy[j] = b_cy[j-1]
                        b_fm[j] = b_fm[j-1]; b_sc[j] = b_sc[j-1]
                    b_cx[k] = cand_cx[i]; b_cy[k] = cand_cy[i]
                    b_fm[k] = cand_fm[i]; b_sc[k] = score
                    b_cnt = max(b_cnt, k + 1)
                    break
    
    return b_fm[0]


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
                bvx[t2] = np.array([bullets[i].vx for i in t2i], dtype=np.float64) / 64.0
                bvy[t2] = np.array([bullets[i].vy for i in t2i], dtype=np.float64) / 64.0
        
        grids = []
        for d in range(DEPTH + 1):
            tf = d * STEP
            grids.append(build_grid(bx + bvx * tf, by + bvy * tf, GX, GY, CELL))
        
        sx = max(0, min(GX - 1, int(px // CELL)))
        sy = max(0, min(GY - 1, int(py // CELL)))
        best = beam_on_grid(grids, sx, sy, GX, GY, DEPTH, BEAM_K)
        
        if best >= 0:
            return int(BITS_ARR[best])
        
        fx, fy = 0.0, 0.0
        for i in range(n):
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
            if dot > bd: bd, bb = dot, BITS_ARR[mi]
        return bb
