"""
ai_beam.py — JIT-compiled Multi-Step Beam Search.

Every frame: simulate 6-step paths (234 total evaluations) with beam width K=5.
Each step evaluates all 9 moves from each of the top-K positions.
Finds the best multi-step path, returns its first move.

~0.3ms/frame → 3000+ FPS effective.
"""

import numpy as np
from numba import njit

MOVES = np.array([
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
], dtype=np.int32)
BITS = np.array([0, 1, 8, 2, 4, 3, 5, 10, 12], dtype=np.int32)

SCR_W, SCR_H = 0x130, 0xE0
CTR_X, CTR_Y = 0x98, 0x2C
SPEED = 1

BEAM_DEPTH = 10     # steps to search (was 6)
BEAM_WIDTH = 8       # top-K paths (was 5)
CHECK_EVERY = 2      # evaluate every N frames (was 4)
# Total: ~657 path evaluations, ~0.12ms with JIT

COLLISION_VAL = 10_000_000.0
PROXIMITY_VAL = 4000.0
CENTER_W = 2.0
WALL_W = 3000.0

# Exact hitbox from decompiled code: 2 <= dx < 13, 0 <= dy < 10
HIT_X1, HIT_X2 = 2.0, 13.0
HIT_Y1, HIT_Y2 = 0.0, 10.0


@njit
def _score_pos(px, py, bullets_t):
    """Score one position against bullets at one frame."""
    B = bullets_t.shape[0]
    min_d2 = 1e30
    for i in range(B):
        dx = bullets_t[i, 0] - px
        dy = bullets_t[i, 1] - py
        if dx >= HIT_X1 and dx < HIT_X2 and dy >= HIT_Y1 and dy < HIT_Y2:
            return COLLISION_VAL, True
        cdx = bullets_t[i, 0] - (px + 7.5)
        cdy = bullets_t[i, 1] - (py + 5.0)
        d2 = cdx * cdx + cdy * cdy
        if d2 < 1.0: d2 = 1.0
        if d2 < min_d2: min_d2 = d2
    s = PROXIMITY_VAL / min_d2
    s += abs(px - CTR_X) * CENTER_W * 0.05
    s += abs(py - CTR_Y) * CENTER_W * 0.05
    if px < 15.0: s += (15.0 - px) * WALL_W
    elif px > SCR_W - 15.0: s += (px - (SCR_W - 15.0)) * WALL_W
    if py < 15.0: s += (15.0 - py) * WALL_W
    elif py > SCR_H - 15.0: s += (py - (SCR_H - 15.0)) * WALL_W
    return s, False


@njit
def _beam_search(px0, py0, paths):
    """
    Multi-step beam search through (x, y, t) space.
    Returns best first-move bitmask index.
    """
    K = BEAM_WIDTH
    DEPTH = BEAM_DEPTH
    T = paths.shape[1]

    # Beam: arrays of (px, py, first_move_idx)
    beam_px = np.zeros(K, dtype=np.float64)
    beam_py = np.zeros(K, dtype=np.float64)
    beam_first = np.zeros(K, dtype=np.int32)
    beam_score = np.full(K, 1e30, dtype=np.float64)
    beam_px[0] = px0
    beam_py[0] = py0
    beam_first[0] = -1
    beam_score[0] = 0.0
    beam_count = 1  # how many active

    step = CHECK_EVERY

    for d in range(DEPTH):
        t = (d + 1) * step
        if t >= T: break
        bullets_t = paths[:, t, :]

        # Expand: each beam element × 9 moves
        candidates_px = np.zeros(K * 9, dtype=np.float64)
        candidates_py = np.zeros(K * 9, dtype=np.float64)
        candidates_first = np.zeros(K * 9, dtype=np.int32)
        candidates_score = np.full(K * 9, 1e30, dtype=np.float64)
        ci = 0

        for bi in range(beam_count):
            for mi in range(9):
                nx = beam_px[bi] + MOVES[mi, 0] * SPEED * step
                ny = beam_py[bi] + MOVES[mi, 1] * SPEED * step
                if nx < 0.0: nx = 0.0
                if nx > SCR_W: nx = float(SCR_W)
                if ny < 0.0: ny = 0.0
                if ny > SCR_H: ny = float(SCR_H)

                s, fatal = _score_pos(nx, ny, bullets_t)
                if fatal:
                    s += 1e9
                w = 1.0 / (0.5 + t * 0.03)
                total = beam_score[bi] + s * w

                candidates_px[ci] = nx
                candidates_py[ci] = ny
                candidates_first[ci] = beam_first[bi] if beam_first[bi] >= 0 else mi
                candidates_score[ci] = total
                ci += 1

        # Keep top K
        top_k = np.argsort(candidates_score[:ci])[:K]
        for ki in range(min(K, len(top_k))):
            idx = top_k[ki]
            beam_px[ki] = candidates_px[idx]
            beam_py[ki] = candidates_py[idx]
            beam_first[ki] = candidates_first[idx]
            beam_score[ki] = candidates_score[idx]
        beam_count = min(K, ci)

    return beam_first[0]


class BeamAI:
    """Multi-step beam search with JIT compilation."""

    def __init__(self, vel_table=None, accel_table=None):
        self.vel_table = np.array(vel_table or [(0, 0)], dtype=np.float32)

    def _velocity(self, angles):
        idx = np.clip((angles & 0x3F).astype(np.int32), 0, len(self.vel_table) - 1)
        return self.vel_table[idx] / 64.0

    def _predict(self, bullets):
        n = len(bullets)
        T = BEAM_DEPTH * CHECK_EVERY + 1
        if n == 0:
            return np.zeros((0, T, 2), dtype=np.float64)
        bx = np.array([b.x for b in bullets], dtype=np.float64)
        by = np.array([b.y for b in bullets], dtype=np.float64)
        ang = np.array([b.angle_index for b in bullets], dtype=np.int32)
        vel = self._velocity(ang)
        ts = np.arange(T, dtype=np.float64)
        paths = np.zeros((n, T, 2), dtype=np.float64)
        paths[:, :, 0] = bx[:, None] + vel[:, 0, None] * ts[None, :]
        paths[:, :, 1] = by[:, None] + vel[:, 1, None] * ts[None, :]
        return paths

    def decide(self, px, py, bullets):
        if not bullets:
            return 0
        if px <= 0 or py <= 0:
            px, py = CTR_X, CTR_Y
        paths = self._predict(bullets)
        return int(BITS[_beam_search(float(px), float(py), paths)])
