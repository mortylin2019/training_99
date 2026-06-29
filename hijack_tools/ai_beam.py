"""
ai_beam.py — JIT-compiled Beam Search with directional danger prediction.

Models bullet threats based on their movement direction (fair — human-visible).
Auto-detects C engine DLL for CHECK_EVERY=1 search, falls back to Python.
Config: see algo_config.py
"""
import numpy as np
from numba import njit
from algo_config import (
    MOVES, BITS, N_ACTIONS, SPEED,
    SCR_W, SCR_H, CTR_X, CTR_Y,
    BEAM_DEPTH, BEAM_WIDTH, CHECK_EVERY,
    C_BEAM_DEPTH, C_CHECK_EVERY,
    COLLISION_VAL, DANGER_BASE, DANGER_DECAY, SAFETY_MARGIN,
    CENTER_PULL, WALL_PENALTY, WALL_MARGIN,
    HIT_X1, HIT_X2, HIT_Y1, HIT_Y2,
    TIME_WEIGHT_BASE, TIME_WEIGHT_RATE,
    USE_INVERSE_SQUARE, USE_COLLISION, USE_CENTER_PULL,
    USE_WALL_PENALTY, USE_SAFETY_MARGIN,
    USE_TIME_WEIGHTING, USE_TIEBREAK,
    USE_C_BEAM,
)

# Convert to numpy arrays for numba JIT
MOVES = np.array(MOVES, dtype=np.int32)
BITS = np.array(BITS, dtype=np.int32)

# Compute effective margins based on toggles
_EFF_MARGIN = SAFETY_MARGIN if USE_SAFETY_MARGIN else 0.0


@njit
def _score_pos(px, py, bullets_t):
    """
    Full danger scoring — used by Python fallback (CHECK_EVERY=4).
    Needs all components for safety at 4px resolution.
    """
    B = bullets_t.shape[0]
    danger = 0.0
    for i in range(B):
        bx = bullets_t[i, 0]
        by = bullets_t[i, 1]
        dx = bx - px; dy = by - py
        # Collision check with safety margin
        if (dx >= HIT_X1 - SAFETY_MARGIN and dx < HIT_X2 + SAFETY_MARGIN
                and dy >= HIT_Y1 - SAFETY_MARGIN and dy < HIT_Y2 + SAFETY_MARGIN):
            return COLLISION_VAL, True
        # Inverse-square danger
        d2 = dx * dx + dy * dy
        if d2 < 4.0: d2 = 4.0
        danger += DANGER_BASE / d2
    # Center pull (Python beam uses proven mild value, ignore config)
    danger += abs(px - CTR_X) * 0.3
    danger += abs(py - CTR_Y) * 0.3
    # Wall penalty
    if px < 10.0: danger += (10.0 - px) * 5000.0
    elif px > SCR_W - 10.0: danger += (px - (SCR_W - 10.0)) * 5000.0
    if py < 10.0: danger += (10.0 - py) * 5000.0
    elif py > SCR_H - 10.0: danger += (py - (SCR_H - 10.0)) * 5000.0
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
                if fatal: s += 1e9
                w = 1.0 / (TIME_WEIGHT_BASE + t * TIME_WEIGHT_RATE)
                tb = ((int(nx * 7919) ^ int(ny * 6271)) & 0xFFF) * 1e-6
                total = beam_score[bi] + s * w + tb

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
    """
    Beam search AI. Uses C engine (CHECK_EVERY=1) when DLL available,
    falls back to Python beam (CHECK_EVERY=4) otherwise.
    """

    def __init__(self, vel_table=None, accel_table=None):
        self.vel_table = np.array(vel_table or [(0, 0)], dtype=np.float32)
        self._c_available = False
        try:
            from hijack_tools.simulator.c_wrapper import CSimulator
            self._c_available = True
        except Exception:
            try:
                from simulator.c_wrapper import CSimulator
                self._c_available = True
            except Exception:
                pass

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

        # ── C engine path (CHECK_EVERY=1, 1px steps) ──
        if USE_C_BEAM and self._c_available:
            active = [(b.x, b.y, b.angle_index) for b in bullets
                      if b.angle_index != 0xFF]
            if active:
                try:
                    from hijack_tools.simulator.c_wrapper import c_beam_search
                except ImportError:
                    from simulator.c_wrapper import c_beam_search
                return c_beam_search(px, py, active)

        # ── Python fallback (CHECK_EVERY=4, 4px steps) ──
        paths = self._predict(bullets)
        return int(BITS[_beam_search(float(px), float(py), paths)])
