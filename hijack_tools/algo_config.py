"""
algo_config.py — Beam Search Algorithm Configuration

Single source of truth for all beam search parameters.
Shared by ai_beam.py (Python) and ai_nn.py.

DESIGN (2026-07-11, optimised pipeline):
    CHECK_EVERY=4 — coarser stepping = implicit smoothing, 160-frame temporal range.
    BEAM_WIDTH=200 — 200 candidates/depth, viable at 7.6ms (reciprocal table + parallel scoring).
    Rust beam_core: reciprocal 1/d² lookup table replaces f64 division.
    beam_search: parallel candidate scoring via rayon (standalone path).
    beam_search_forced: sequential scoring (called inside 9-way rayon in multi_beam).
    No direction persistence (no soft-commit, no strategic escape).
    No spawn prediction (keeps things fair — no future knowledge).

BEAM WIDTH:
    W=200: 200 candidates per depth → 1800 scored positions/step (viable at 7.6ms).
    W=12 was the old default (1.8ms) before reciprocal table + parallel scoring.
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
BEAM_DEPTH   = 40       # frames of lookahead (0.5s — distant bullets negligible, ≥10 == ≥120)
BEAM_WIDTH   = 200      # top-K paths per depth (200 = viable at 7.6ms with recip+parallel)
CHECK_EVERY  = 4        # frames per beam step (4 = proven optimal, experiment_log §final)

# ── Scoring weights ────────────────────────────────────────
COLLISION_VAL = 1e8          # fatal: in hitbox = instant discard
DANGER_BASE   = 3000.0       # inverse-square danger per bullet (3000 > 2000: more cautious)
SAFETY_MARGIN = 2.0          # extra px clearance around hitbox
DIRECTIONAL_WEIGHT = 1.0     # extra danger for bullets moving toward player (0=off)
CENTER_PULL   = 0.3          # hardcoded in _score_pos — do not change
WALL_PENALTY  = 5000.0       # penalty for being near screen edge
WALL_MARGIN   = 20.0         # px from edge where penalty starts (20 > 40: less wall-avoidance, more dodging)

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

# ── MCTS parameters (used by ai_mcts.py) ─────────────────────
MCTS_ITERATIONS      = 1000     # total guided-rollout iterations across candidates
MCTS_TOP_K           = 3        # max candidates from heuristic filter
MCTS_TAU_START       = 5.0      # annealing start temperature (exploration)
MCTS_TAU_END         = 0.5      # annealing end temperature (exploitation)
MCTS_VERIFY_TAU      = 0.3      # low temperature for candidate verification rollouts
# ── Scoring toggles ────────────────────────────────────────
MULTI_BEAM_ENABLED   = True     # 9 parallel beams, each locked to different first move
EARLY_EXIT_ENABLED  = True     # stop bullet loop when candidate can't win
EARLY_EXIT_BUFFER   = 50000    # safety margin for early exit (max bullet danger)
PARTIAL_SORT_ENABLED = True    # insertion-based top-K vs np.argsort
CENTER_PULL_ENABLED  = True    # gentle pull toward screen center (0.3 weight)
WALL_PENALTY_ENABLED = True    # penalty for approaching screen edges
