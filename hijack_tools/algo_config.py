"""
algo_config.py — Beam Search Algorithm Configuration

Single source of truth for all beam search parameters.
Shared by ai_beam.py (Python) and ai_nn.py.

DESIGN (2026-07-11, simplified pipeline):
    CHECK_EVERY=1 — every frame is a beam step. No intermediate checks needed.
    No direction persistence (no soft-commit, no strategic escape).
    No short-circuit (beam search runs every frame).
    No spawn prediction (keeps things fair — no future knowledge).
    Pure 1/r² + wall/center scoring, beam search every frame.

BEAM WIDTH:
    K=12: fast but prunes escape paths too early (paths ranked 15th at depth 2).
    K=50: preserves escape diversity but 4× cost. Tension between speed and safety.
"""

# ── Movement ───────────────────────────────────────────────
MOVES = [
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
]
BITS = [0, 1, 8, 2, 4, 3, 5, 10, 12]
N_ACTIONS = 9
SPEED = 1  # px/frame (game constant, do not change)

# ── Screen geometry ────────────────────────────────────────
SCR_W, SCR_H = 0x130, 0xE0    # 304 × 224 pixels
CTR_X, CTR_Y = 0x98, 0x70     # 152, 112 — screen center (304/2, 224/2)

# ── Hitbox (from decompiled Stage2_GameEntityLoop.c) ───────
HIT_X1, HIT_X2 = 2.0, 13.0    # 11px wide
HIT_Y1, HIT_Y2 = 0.0, 10.0    # 10px tall

# ── Beam search parameters ─────────────────────────────────
BEAM_DEPTH   = 120      # frames of lookahead (1.5 seconds at 80 FPS)
BEAM_WIDTH   = 12       # top-K paths per depth
CHECK_EVERY  = 1        # frames per beam step (1 = every frame, finest control)

# ── Scoring weights ────────────────────────────────────────
COLLISION_VAL = 1e8          # fatal: in hitbox = instant discard
DANGER_BASE   = 2000.0       # inverse-square danger per bullet
SAFETY_MARGIN = 2.0          # extra px clearance around hitbox
CENTER_PULL   = 0.3          # hardcoded in _score_pos — do not change
WALL_PENALTY  = 5000.0       # penalty for being near screen edge
WALL_MARGIN   = 40.0         # px from edge where penalty starts (early warning)

# ── Time weighting (uniform — all frames equal) ────────────
TIME_WEIGHT_BASE = 0.5       # w = 1 / (base + t * rate)
TIME_WEIGHT_RATE = 0.0       # 0.0 = uniform, >0 = myopic (further future = lower weight)

USE_SAFETY_MARGIN = True     # extra clearance around hitbox
USE_MC_SEARCH = False        # Monte Carlo depth-first sampling

# ── Type-aware bullet prediction ───────────────────────────
USE_TYPE_PREDICTION = False  # True = per-type physics (homing re-aim, accel, steer)
# When False: all bullets predicted via simple linear VEL_TABLE[angle] extrapolation.
# When True:  Type 1 re-aims toward (px,py), Type 2 steers, Type 3 uses ACCEL_TABLE.
# False is faster and simpler; True adds accuracy at cost of Python for-loops per frame.

# ── Scoring toggles ────────────────────────────────────────
EARLY_EXIT_ENABLED  = True     # stop bullet loop when candidate can't win
EARLY_EXIT_BUFFER   = 50000    # safety margin for early exit (max bullet danger)
PARTIAL_SORT_ENABLED = True    # insertion-based top-K vs np.argsort
CENTER_PULL_ENABLED  = True    # gentle pull toward screen center (0.3 weight)
WALL_PENALTY_ENABLED = True    # penalty for approaching screen edges
