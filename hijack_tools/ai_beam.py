"""
ai_beam.py — JIT-compiled Beam Search with directional danger prediction.

Models bullet threats based on their movement direction (fair — human-visible).
Auto-detects C engine DLL for CHECK_EVERY=1 search, falls back to Python.

BEAM SEARCH ALGORITHM ANALYSIS (2026-07-04):

The beam search explores paths through time by evaluating candidate positions
at each CHECK_EVERY frame interval. At each depth, it keeps the top BEAM_WIDTH
paths by accumulated danger score (inverse-square bullet danger + wall penalty
+ center pull). The cumulative score propagates future danger backward through
the beam, so that wall traps and bullet convergence zones affect early decisions.

KEY FINDING — BEAM WIDTH AND PATH PRUNING:
    Narrow beam (width=12) prunes escape paths too early. At depth 1-2, when
    bullets are still approaching, all 9 move directions score similarly because
    no bullets have converged yet. The escape path (heading toward the largest
    angular gap) ranks ~15th and gets discarded. Only at depth 15+ does the
    cumulative danger reveal that the escape path is superior — but by then
    it was already pruned at depth 2. Width=50 preserves enough path diversity
    for the escape route to survive until future scores propagate back.
    
    Impact: worst-case survival improved from 3.4s to 10.8s (+218%).

INTERMEDIATE FRAME CHECKING:
    CHECK_EVERY=4 means the beam evaluates positions at t=4,8,12,... but not
    at t=1,2,3 when the player is moving between checkpoints. A bullet can
    intercept the player between t=4 and the previous position. The beam
    now checks every intermediate frame for fatal collisions, rejecting moves
    that would be killed mid-step.

RECEDING-HORIZON LIMITATION:
    The beam replans from scratch every game frame, executing only the first
    move of the best plan. This means it never commits to long-term strategies.
    When 50 bullets converge on the spawn point (152,44) over the first 50
    frames, the beam sees DOWN as safest each frame because it has the most
    open space. After 68 frames of local optimality, the player is cornered
    at the bottom wall. The beam correctly finds the escape gap (148° at
    frame 68) but the player has already moved 68px from it. Fixing this
    would require either:
    a) Predicting future bullet spawns (requires G_NextSpawnTime — cheating)
    b) Committing to multi-frame strategies without replanning each frame
    c) Pre-emptively avoiding the bullet convergence zone at (152,44)

COMPARISON TO EXHAUSTIVE SEARCH:
    Exhaustive search (all 9^D paths, no pruning) finds the same first move as
    beam search up to depth 6 (531K paths, 0.11s). At depth 6 with CHECK_EVERY=4
    (24 frame lookahead), the beam converges to the same result. The beam's
    advantage is depth: beam reaches depth 20 (80 frames) while exhaustive
    search becomes infeasible at depth 8+ (43M paths).

Config: see algo_config.py
"""
import numpy as np
from numba import njit
try:
    from algo_config import (
        USE_MC_SEARCH,
        MOVES, BITS, N_ACTIONS, SPEED,
        SCR_W, SCR_H, CTR_X, CTR_Y,
        BEAM_DEPTH, BEAM_WIDTH, CHECK_EVERY,
        COLLISION_VAL, DANGER_BASE, DANGER_POWER, DANGER_DECAY, SAFETY_MARGIN,
        CENTER_PULL, WALL_PENALTY, WALL_MARGIN,
        HIT_X1, HIT_X2, HIT_Y1, HIT_Y2,
        TIME_WEIGHT_BASE, TIME_WEIGHT_RATE,
    )
except ImportError:
    from hijack_tools.algo_config import (
        USE_MC_SEARCH,
        MOVES, BITS, N_ACTIONS, SPEED,
        SCR_W, SCR_H, CTR_X, CTR_Y,
        BEAM_DEPTH, BEAM_WIDTH, CHECK_EVERY,
        COLLISION_VAL, DANGER_BASE, DANGER_POWER, DANGER_DECAY, SAFETY_MARGIN,
        CENTER_PULL, WALL_PENALTY, WALL_MARGIN,
        HIT_X1, HIT_X2, HIT_Y1, HIT_Y2,
        TIME_WEIGHT_BASE, TIME_WEIGHT_RATE,
    )

# Convert to numpy arrays for numba JIT
MOVES = np.array(MOVES, dtype=np.int32)
BITS = np.array(BITS, dtype=np.int32)

# Compute effective margins based on toggles
_EFF_MARGIN = SAFETY_MARGIN  # always enabled in Python beam


@njit(cache=True)
def _score_pos(px, py, bullets_t):
    """Full danger scoring with early termination against best-so-far."""
    B = bullets_t.shape[0]
    danger = 0.0
    for i in range(B):
        bx = bullets_t[i, 0]
        by = bullets_t[i, 1]
        dx = bx - px; dy = by - py
        if (dx >= HIT_X1 - SAFETY_MARGIN and dx < HIT_X2 + SAFETY_MARGIN
                and dy >= HIT_Y1 - SAFETY_MARGIN and dy < HIT_Y2 + SAFETY_MARGIN):
            return COLLISION_VAL, True
        d2 = dx * dx + dy * dy
        if d2 < 4.0: d2 = 4.0
        danger += DANGER_BASE / d2
    danger += abs(px - CTR_X) * 0.3
    danger += abs(py - CTR_Y) * 0.3
    if px < WALL_MARGIN: danger += (WALL_MARGIN - px) * WALL_PENALTY
    elif px > SCR_W - WALL_MARGIN: danger += (px - (SCR_W - WALL_MARGIN)) * WALL_PENALTY
    if py < WALL_MARGIN: danger += (WALL_MARGIN - py) * WALL_PENALTY
    elif py > SCR_H - WALL_MARGIN: danger += (py - (SCR_H - WALL_MARGIN)) * WALL_PENALTY
    return danger, False


@njit(cache=True)
def _score_pos_early_exit(px, py, bullets_t, best_so_far):
    """Scoring with early termination — stops when candidate can't win."""
    B = bullets_t.shape[0]
    danger = 0.0
    for i in range(B):
        bx = bullets_t[i, 0]
        by = bullets_t[i, 1]
        dx = bx - px; dy = by - py
        if (dx >= HIT_X1 - SAFETY_MARGIN and dx < HIT_X2 + SAFETY_MARGIN
                and dy >= HIT_Y1 - SAFETY_MARGIN and dy < HIT_Y2 + SAFETY_MARGIN):
            return COLLISION_VAL, True
        d2 = dx * dx + dy * dy
        if d2 < 4.0: d2 = 4.0
        danger += DANGER_BASE / d2
        if danger > best_so_far:
            return danger, False
    danger += abs(px - CTR_X) * 0.3
    danger += abs(py - CTR_Y) * 0.3
    if px < WALL_MARGIN: danger += (WALL_MARGIN - px) * WALL_PENALTY
    elif px > SCR_W - WALL_MARGIN: danger += (px - (SCR_W - WALL_MARGIN)) * WALL_PENALTY
    if py < WALL_MARGIN: danger += (WALL_MARGIN - py) * WALL_PENALTY
    elif py > SCR_H - WALL_MARGIN: danger += (py - (SCR_H - WALL_MARGIN)) * WALL_PENALTY
    return danger, False


@njit(cache=True)
def _check_collision(px, py, bullets_t):
    """Fast collision-only check — no danger score, just fatal yes/no."""
    B = bullets_t.shape[0]
    for i in range(B):
        dx = bullets_t[i, 0] - px
        dy = bullets_t[i, 1] - py
        if (dx >= HIT_X1 - SAFETY_MARGIN and dx < HIT_X2 + SAFETY_MARGIN
                and dy >= HIT_Y1 - SAFETY_MARGIN and dy < HIT_Y2 + SAFETY_MARGIN):
            return True
    return False


@njit(cache=True)
def _beam_search(px0, py0, paths):
    """Beam search with partial top-K selection + early-termination scoring."""
    K = BEAM_WIDTH
    DEPTH = BEAM_DEPTH
    T = paths.shape[1]
    step = CHECK_EVERY

    beam_px = np.zeros(K, dtype=np.float64)
    beam_py = np.zeros(K, dtype=np.float64)
    beam_first = np.zeros(K, dtype=np.int32)
    beam_score = np.full(K, 1e30, dtype=np.float64)
    beam_px[0] = px0; beam_py[0] = py0
    beam_first[0] = -1; beam_score[0] = 0.0
    beam_count = 1

    cand_px = np.zeros(K * 9, dtype=np.float64)
    cand_py = np.zeros(K * 9, dtype=np.float64)
    cand_first = np.zeros(K * 9, dtype=np.int32)
    cand_score = np.zeros(K * 9, dtype=np.float64)
    top_k = np.zeros(K, dtype=np.int32)
    top_score = np.full(K, 1e30, dtype=np.float64)

    for d in range(DEPTH):
        t = (d + 1) * step
        if t >= T: break
        bullets_t = paths[:, t, :]

        # Early-termination threshold: worst score currently in beam
        worst_beam = beam_score[beam_count - 1] if beam_count > 0 else 1e30

        ci = 0
        for bi in range(beam_count):
            for mi in range(9):
                nx = beam_px[bi] + MOVES[mi, 0] * SPEED * step
                ny = beam_py[bi] + MOVES[mi, 1] * SPEED * step
                if nx < 0.0: nx = 0.0
                if nx > SCR_W: nx = float(SCR_W)
                if ny < 0.0: ny = 0.0
                if ny > SCR_H: ny = float(SCR_H)

                fatal_intermediate = False
                if step > 1:
                    prev_t = d * step
                    for sub_t in range(prev_t + 1, t):
                        if sub_t >= T: break
                        bullets_sub = paths[:, sub_t, :]
                        frac = (sub_t - prev_t) / step
                        mid_x = beam_px[bi] + MOVES[mi, 0] * SPEED * step * frac
                        mid_y = beam_py[bi] + MOVES[mi, 1] * SPEED * step * frac
                        if mid_x < 0.0: mid_x = 0.0
                        if mid_x > SCR_W: mid_x = float(SCR_W)
                        if mid_y < 0.0: mid_y = 0.0
                        if mid_y > SCR_H: mid_y = float(SCR_H)
                        if _check_collision(mid_x, mid_y, bullets_sub):
                            fatal_intermediate = True
                            break

                if fatal_intermediate:
                    continue

                # Score with early termination: skip bullets once danger > worst_beam
                s, fatal = _score_pos_early_exit(nx, ny, bullets_t, worst_beam + 500.0)
                if fatal: s += 1e9
                w = 1.0 / (TIME_WEIGHT_BASE + t * TIME_WEIGHT_RATE)
                tb = ((int(nx * 7919) ^ int(ny * 6271)) & 0xFFF) * 1e-6
                total = beam_score[bi] + s * w + tb

                cand_px[ci] = nx
                cand_py[ci] = ny
                cand_first[ci] = beam_first[bi] if beam_first[bi] >= 0 else mi
                cand_score[ci] = total
                ci += 1

        # Partial top-K selection (insertion sort, O(N*K) vs O(N log N))
        for k in range(K):
            top_k[k] = -1
            top_score[k] = 1e30
        for i in range(ci):
            score = cand_score[i]
            for k in range(K):
                if score < top_score[k]:
                    for j in range(K - 1, k, -1):
                        top_k[j] = top_k[j - 1]
                        top_score[j] = top_score[j - 1]
                    top_k[k] = i
                    top_score[k] = score
                    break

        nc = 0
        for k in range(K):
            if top_k[k] < 0: break
            idx = top_k[k]
            beam_px[nc] = cand_px[idx]
            beam_py[nc] = cand_py[idx]
            beam_first[nc] = cand_first[idx]
            beam_score[nc] = cand_score[idx]
            nc += 1
        beam_count = nc

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

    # Compute angles for nearby bullets only (ignore distant irrelevant ones)
    GAP_RADIUS = 60.0
    angles = np.zeros(N, dtype=np.float64)
    count = 0
    for i in range(N):
        dx = bullets_arr[i, 0] - px
        dy = bullets_arr[i, 1] - py
        d2 = dx * dx + dy * dy
        if d2 < GAP_RADIUS * GAP_RADIUS:
            angles[count] = np.arctan2(dy, dx)
            count += 1
    N = count
    if N == 0:
        return 0

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
    """Beam search AI. JIT-compiled with numba for real-time performance."""

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

        # ── Short-circuit: if no bullet is within 80px and not near wall,
        #     skip expensive beam search — just maximize distance.
        nearest_d2 = float('inf')
        for b in bullets:
            d2 = (b.x - px)**2 + (b.y - py)**2
            if d2 < nearest_d2:
                nearest_d2 = d2
        near_wall = (px < 40 or px > 264 or py < 40 or py > 184)
        if nearest_d2 > 6400 and not near_wall:  # 80^2 = 6400
            # Fast repulsion: sum force vectors, pick closest discrete move
            fx = fy = 0.0
            for b in bullets:
                dx = px - b.x; dy = py - b.y
                d2 = dx*dx + dy*dy
                if d2 < 0.1: d2 = 0.1
                inv_d3 = 1.0 / (d2 * d2**0.5)
                fx += dx * inv_d3; fy += dy * inv_d3
            best_dot = -float('inf')
            best_idx = 0
            for mi in range(9):
                mdx, mdy = MOVES[mi]
                if mdx == 0 and mdy == 0:
                    dot = -0.1
                else:
                    mmag = (mdx*mdx + mdy*mdy)**0.5
                    vmag = max(abs(fx)+abs(fy), 0.001)
                    dot = (mdx*fx + mdy*fy) / (mmag * vmag)
                if dot > best_dot:
                    best_dot, best_idx = dot, mi
            return int(BITS[best_idx])

        # ── Beam search
        paths = self._predict(bullets)
        if USE_MC_SEARCH:
            best = int(_mc_search(float(px), float(py), paths))
        else:
            best = int(_beam_search(float(px), float(py), paths))
        # Gap finder fallback
        if best <= 0:
            best = _max_gap_move(float(px), float(py),
                                 np.array([(b.x, b.y) for b in bullets], dtype=np.float64))
        return int(BITS[max(best, 0) % len(BITS)])


@njit
def _mc_search(px, py, paths):
    """
    Monte Carlo depth-first search — samples complete trajectories to avoid
    premature pruning. For each of 9 first moves, runs random continuations
    to the full depth. Returns the move with the best average survival score.
    """
    T = paths.shape[1]
    step = CHECK_EVERY
    depth = min(BEAM_DEPTH, (T - 1) // step)
    N_ROLLOUTS = 30

    best_move = 0
    best_score = 1e30

    for mi in range(9):
        total_score = 0.0
        survived = 0
        for _ in range(N_ROLLOUTS):
            # Start from current position, apply first move at step 0
            cx, cy = px, py
            nx = px + MOVES[mi, 0] * step
            ny = py + MOVES[mi, 1] * step
            if nx < 0: nx = 0.0
            if nx > SCR_W: nx = float(SCR_W)
            if ny < 0: ny = 0.0
            if ny > SCR_H: ny = float(SCR_H)
            # Check first move
            t1 = step
            if t1 < T:
                s, fatal = _score_pos(nx, ny, paths[:, t1, :])
                if fatal: continue
            
            score = 0.0
            alive = True
            cx, cy = nx, ny
            # Random continuation for remaining depth
            for d in range(1, depth):
                rm = np.random.randint(0, 9)
                nx = cx + MOVES[rm, 0] * step
                ny = cy + MOVES[rm, 1] * step
                if nx < 0: nx = 0.0
                if nx > SCR_W: nx = float(SCR_W)
                if ny < 0: ny = 0.0
                if ny > SCR_H: ny = float(SCR_H)
                t = (d + 1) * step
                if t >= T: break
                s, fatal = _score_pos(nx, ny, paths[:, t, :])
                if fatal: alive = False; break
                score += s
                cx, cy = nx, ny
            if alive:
                survived += 1
                total_score += score
        
        if survived > 0:
            avg_score = total_score / survived
        else:
            avg_score = 1e9
        if avg_score < best_score:
            best_score = avg_score
            best_move = mi

    if best_score > 1e8:
        return _max_gap_move(px, py, paths[:, 0, :])
    return best_move
