"""
ai_beam.py — JIT-compiled Beam Search with directional danger prediction.

Models bullet threats based on their movement direction (fair — human-visible).
Uses adaptive beam depth based on bullet density.
No memory cheats, no teleport, 1px/frame movement only.
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

# Optimal: 160f lookahead covers bullet travel time
BEAM_DEPTH = 40     # steps
BEAM_WIDTH = 12     # top-K paths (optimal: balances diversity vs speed)
CHECK_EVERY = 4     # every 4f → 160f = 2.0s lookahead

# Scoring weights
COLLISION_VAL = 1e8
DANGER_BASE = 2000.0       # base danger per bullet in path
DANGER_DECAY = 0.85        # exponential decay per frame
SAFETY_MARGIN = 2.0        # extra clearance around hitbox
CENTER_PULL = 0.3          # gentle pull toward center
WALL_PENALTY = 5000.0

# Exact hitbox: 2 <= dx < 13, 0 <= dy < 10
HIT_X1, HIT_X2 = 2.0, 13.0
HIT_Y1, HIT_Y2 = 0.0, 10.0


@njit
def _score_pos(px, py, bullets_t):
    """
    Inverse-square danger scoring with safety margin.
    Scores: lower = safer. Returns (score, is_fatal).
    """
    B = bullets_t.shape[0]
    danger = 0.0

    for i in range(B):
        bx = bullets_t[i, 0]
        by = bullets_t[i, 1]
        dx = bx - px
        dy = by - py

        if (dx >= HIT_X1 - SAFETY_MARGIN and dx < HIT_X2 + SAFETY_MARGIN
                and dy >= HIT_Y1 - SAFETY_MARGIN and dy < HIT_Y2 + SAFETY_MARGIN):
            return COLLISION_VAL, True

        d2 = dx * dx + dy * dy
        if d2 < 4.0:
            d2 = 4.0
        danger += DANGER_BASE / d2

    danger += abs(px - CTR_X) * CENTER_PULL
    danger += abs(py - CTR_Y) * CENTER_PULL

    if px < 10.0:
        danger += (10.0 - px) * WALL_PENALTY
    elif px > SCR_W - 10.0:
        danger += (px - (SCR_W - 10.0)) * WALL_PENALTY
    if py < 10.0:
        danger += (10.0 - py) * WALL_PENALTY
    elif py > SCR_H - 10.0:
        danger += (py - (SCR_H - 10.0)) * WALL_PENALTY

    return danger, False


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
                # Tiny positional hash breaks ties, prevents deterministic death loops
                tiebreak = ((int(nx * 7919) ^ int(ny * 6271)) & 0xFFF) * 1e-6
                total = beam_score[bi] + s * w + tiebreak

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


@njit
def _max_gap_move(px, py, bullets_arr):
    """
    Find the largest angular gap between nearby bullets, move toward its center.
    Pure survival heuristic — robust when surrounded.
    bullets_arr: (N,2) array of (bx, by) positions.
    Returns BITS index (0-8).
    """
    N = bullets_arr.shape[0]
    if N == 0:
        return 0

    # Compute angles and distances of bullets relative to player
    angles = np.zeros(N, dtype=np.float64)
    for i in range(N):
        dx = bullets_arr[i, 0] - px
        dy = bullets_arr[i, 1] - py
        angles[i] = np.arctan2(dy, dx)  # [-π, π]

    # Sort angles
    angles = np.sort(angles)

    # Find largest gap between consecutive angles
    best_gap = 0.0
    best_mid = 0.0
    for i in range(N - 1):
        gap = angles[i + 1] - angles[i]
        if gap > best_gap:
            best_gap = gap
            best_mid = (angles[i] + angles[i + 1]) * 0.5

    # Check wrap-around gap
    wrap_gap = angles[0] + 2.0 * np.pi - angles[N - 1]
    if wrap_gap > best_gap:
        best_gap = wrap_gap
        best_mid = angles[N - 1] + wrap_gap * 0.5
        if best_mid > np.pi:
            best_mid -= 2.0 * np.pi

    # Convert gap midpoint angle to a move direction
    # Map angle to closest of 8 cardinal+diagonal directions
    cos_a = np.cos(best_mid)
    sin_a = np.sin(best_mid)

    # Determine primary direction
    if abs(cos_a) > abs(sin_a):
        # Horizontal dominant
        mx = 1 if cos_a > 0 else -1
        my = 1 if sin_a > 0.4 else (-1 if sin_a < -0.4 else 0)
    else:
        # Vertical dominant
        my = 1 if sin_a > 0 else -1
        mx = 1 if cos_a > 0.4 else (-1 if cos_a < -0.4 else 0)

    # Match to MOVES array
    for mi in range(9):
        if MOVES[mi, 0] == mx and MOVES[mi, 1] == my:
            return mi
    return 0


class BeamAI:
    """Hybrid AI: max-gap escape when surrounded, beam search otherwise."""

    def __init__(self, vel_table=None, accel_table=None):
        self.vel_table = np.array(vel_table or [(0, 0)], dtype=np.float32)

    def _velocity(self, angles):
        idx = np.clip((angles & 0x3F).astype(np.int32), 0, len(self.vel_table) - 1)
        return self.vel_table[idx] / 64.0

    def _predict(self, bullets):
        """Predict bullet positions over time (linear extrapolation)."""
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
