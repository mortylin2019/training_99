"""
algo_config.py — Beam Search Algorithm Configuration

Single source of truth for all beam search parameters.
Shared by ai_beam.py (Python) and c_engine.c (C) — keep in sync.
"""

# ── Movement ───────────────────────────────────────────────
# 9-direction movement: STOP, LEFT, RIGHT, UP, DOWN, UL, UR, DL, DR
MOVES = [
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
]
BITS = [0, 1, 8, 2, 4, 3, 5, 10, 12]
N_ACTIONS = 9
SPEED = 1  # px/frame (game constant, do not change)

# ── Screen geometry ────────────────────────────────────────
SCR_W, SCR_H = 0x130, 0xE0    # 304 × 224 pixels
CTR_X, CTR_Y = 0x98, 0x2C     # 152, 44 — player spawn

# ── Hitbox (from decompiled Stage2_GameEntityLoop.c) ───────
HIT_X1, HIT_X2 = 2.0, 13.0    # 11px wide
HIT_Y1, HIT_Y2 = 0.0, 10.0    # 10px tall

# ── Beam search parameters ─────────────────────────────────
# Total lookahead = BEAM_DEPTH × CHECK_EVERY frames
# At 80 FPS: 160 frames = 2.0 seconds
#
# Python path (no C DLL): CHECK_EVERY=4, DEPTH=40
# C engine path:          CHECK_EVERY=1, DEPTH=160
BEAM_DEPTH   = 40       # search steps (increased to 160 when C engine used)
BEAM_WIDTH   = 12       # top-K paths kept at each depth
CHECK_EVERY  = 4        # frames per beam step (1 when C engine available)

# Overrides when C engine beam search is active
C_BEAM_DEPTH  = 160     # 2.0s at 80 FPS, 1px steps
C_CHECK_EVERY = 1       # pixel-perfect paths

# ── Scoring weights ────────────────────────────────────────
COLLISION_VAL = 1e8          # fatal: in hitbox = instant discard
DANGER_BASE   = 2000.0       # inverse-square danger per bullet
DANGER_POWER  = 2            # 1=1/r, 2=1/r²
DANGER_DECAY  = 0.85         # time decay per frame (earlier danger counts less)
SAFETY_MARGIN = 2.0          # extra px clearance around hitbox
CENTER_PULL   = 5.0          # attraction toward (CTR_X, CTR_Y) — strong!
WALL_PENALTY  = 5000.0       # penalty for being near screen edge
WALL_MARGIN   = 10.0         # px from edge where penalty starts

# ── Time weighting ─────────────────────────────────────────
TIME_WEIGHT_BASE = 0.5       # w = 1 / (base + t * rate)
TIME_WEIGHT_RATE = 0.03      # farther future = lower weight

# ── Scoring toggles (True = enabled, False = disabled) ─────
# Toggle individual scoring components to find optimal combination.
# These affect both Python and C beam search paths.
USE_INVERSE_SQUARE = True    # 1/d² danger from bullets (core mechanic)
USE_COLLISION      = True    # instant-death hitbox check
USE_CENTER_PULL    = True    # gentle pull toward screen center
USE_WALL_PENALTY   = True    # penalty for being near edges
USE_SAFETY_MARGIN  = True    # extra clearance around hitbox
USE_TIME_WEIGHTING = True    # farther future = lower weight (w = 1/(base+t*rate))
USE_TIEBREAK       = True    # deterministic tiebreak to avoid death loops

# ── Engine selection ───────────────────────────────────────
# When True, uses C beam search (CHECK_EVERY=1, fast, experimental).
# When False, uses Python numba beam (CHECK_EVERY=4, proven 72s).
USE_C_BEAM = True
# These are informational — actual values live in c_engine.c
# BS_DEPTH=160, BS_WIDTH=12, BS_CHECK=1, BS_MAX_B=150
# Scoring toggles in C: search for // ── Scoring toggles ── in c_engine.c
