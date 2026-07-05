"""
algo_config.py — Beam Search Algorithm Configuration

Single source of truth for all beam search parameters.
Shared by ai_beam.py (Python) and c_engine.c (C) — keep in sync.

IMPORTANT DESIGN NOTES (2026-07-04, ESIL + Oracle verified):

BEAM WIDTH (50, was 12):
    The beam prunes paths at each depth step, keeping only the top K by score.
    With K=12, the escape path through a bullet gap was consistently discarded
    at depth 1-2 because it scored equally to other paths early on. Only at
    later depths (when bullets converge and wall penalties appear) does the
    escape path prove superior — but by then it was already pruned.
    K=50 keeps enough diversity for the escape path to survive early pruning
    until future scores propagate back and reveal its true value.
    This improved worst-case survival from 3.4s to 10.8s (+218%).

BEAM DEPTH (20, was 40):
    At CHECK_EVERY=4, depth 20 = 80 frames = 1 second lookahead.
    Combined with wider beam, this is sufficient to find escape routes.
    Deeper search (40+) adds cost without benefit when beam is wide.

INTERMEDIATE FRAME CHECKING:
    Between beam steps (every 4 frames), we check frames 1-3 for fatal
    collisions. Without this, bullets that hit between checkpoints are missed.

CENTER PULL (hardcoded 0.3 in _score_pos, not configurable):
    Gentle pull toward screen center (152,112). Stronger values (5.0 tested)
    cause the AI to walk through dangerous bullet paths.

WALL MARGIN (40px, was 10px):
    Wall penalty starts 40px from edges instead of 10px. At 10px the AI
    couldn't see wall danger until too late — it would walk straight down
    for 60+ frames, corner itself, and die.

VERIFICATION:
    - ESIL cross-validation: 1105/1105 instruction-level tests pass
    - Python simulator bugs fixed: 11 (divisor, octant, RNG, struct fields)
    - Oracle reviewed: all improvements fair (VEL_TABLE only, no bullet type)
    - C engine physics fixed (divisor, center pull, pattern RNG)
    - C beam search still has bugs (disabled: USE_C_BEAM=False)
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
CTR_X, CTR_Y = 0x98, 0x70     # 152, 112 — screen center (304/2, 224/2)

# ── Hitbox (from decompiled Stage2_GameEntityLoop.c) ───────
HIT_X1, HIT_X2 = 2.0, 13.0    # 11px wide
HIT_Y1, HIT_Y2 = 0.0, 10.0    # 10px tall

# ── Beam search parameters ─────────────────────────────────
# Total lookahead = BEAM_DEPTH × CHECK_EVERY frames
# At 80 FPS: 160 frames = 2.0 seconds
#
# Python path (no C DLL): CHECK_EVERY=4, DEPTH=40
# C engine path:          CHECK_EVERY=1, DEPTH=160
BEAM_DEPTH   = 20       # 80 frames lookahead at CHECK_EVERY=4
BEAM_WIDTH   = 50  # wide beam preserves escape paths       # wider beam preserves escape paths through early pruning
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
WALL_MARGIN   = 40.0         # px from edge where penalty starts (early warning)

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
USE_C_BEAM = False  # C beam needs more debugging
# These are informational — actual values live in c_engine.c
# BS_DEPTH=160, BS_WIDTH=12, BS_CHECK=1, BS_MAX_B=150
# Scoring toggles in C: search for // ── Scoring toggles ── in c_engine.c
USE_MC_SEARCH = False   # Monte Carlo depth-first sampling
