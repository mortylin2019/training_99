"""
simulator/config.py — Centralized constants matching decompiled 99.exe.
All values verified against reverse_engineering_ref/decompiled/99.exe.c.
Single source of truth — imported by engine.py, bullet.py, runner.py.
"""

# ── Screen & World ──────────────────────────────────────────
SCR_W = 0x130       # 304 pixels
SCR_H = 0xE0        # 224 pixels
# Off-screen thresholds (C: raw_x < 0x5101, raw_y < 0x3d01 for ON-screen)
RAW_MAX_X = 0x5101
RAW_MAX_Y = 0x3D01
MAX_ENTITIES = 300
MAX_BULLETS = 299       # C: DAT_00406da8 < 299

# ── Player ───────────────────────────────────────────────────
PLAYER_START_X = 0x98   # 152 px
PLAYER_START_Y = 0x2C   # 44 px
HIT_X1, HIT_X2 = 2, 13  # C: dx >= 2, dx < 13 (iVar4 - 2U < 0xb)
HIT_Y1, HIT_Y2 = 0, 10  # C: dy >= 0, dy < 10 (uVar8 < 10)
PLAYER_CENTER = 6        # C: player + 6 offset for aim target

# ── Graze System ─────────────────────────────────────────────
GRAZE_DX = 23           # C: dx + 4 < 0x17
GRAZE_DY = 20           # C: dy + 6 < 0x14
GRAZE_CHAIN_MS = 1000   # C: DAT_00406e08 = uVar2 + 1000
GRAZE_CHAIN_MAX = 10    # C: DAT_00406e0c < 10

# ── Spawn System ─────────────────────────────────────────────
SPAWN_INTERVAL_MS = 3000  # C: DAT_00406dfc = uVar2 + 0xBB8 (3000ms). Assembly verified at 0x40334D
SPAWN_EDGES = 4

# ── Pattern System ───────────────────────────────────────────
PATTERN_CHECK_MS = 5000     # C: DAT_00406e00 = uVar2 + 5000 (cooldown/retry)
PATTERN_ACTIVE_MS = 10000   # C: DAT_00406e00 = uVar2 + 10000 (pattern active)
PATTERN_DURATION = 100      # C: _DAT_00406db0 = 100 (display counter)
PATTERN_CHANCE = 0x3000     # C: if (uVar6 < 0x3000) — 37.5% of 0x8000

# Per-pattern spawn info: (type, timer, spread)
# Spread: ±(spread/2) angle jitter (0 = perfect aim)
# Timer: homing re-target interval (0 = no homing)
PATTERN_INFO = {
    0: {"type": 0, "timer": 0, "spread": 5},      # Normal, no pattern
    1: {"type": 0, "timer": 0, "spread": 0},      # Normal, PERFECT aim!
    2: {"type": 1, "timer": 0x30, "spread": 5},   # Homing, 48f re-target
    3: {"type": 1, "timer": 0x20, "spread": 5},   # Homing, 32f
    4: {"type": 1, "timer": 0x10, "spread": 5},   # Homing, 16f
    5: {"type": 1, "timer": 0, "spread": 5},      # Homing, random timer
    6: {"type": 3, "timer": 0, "spread": 5},      # Accelerating
    7: {"type": 2, "timer": 0, "spread": 0},      # H-Accel, no aiming
}
# Homing re-target spread (C: FUN_00402d68(ECX, 3))
HOMING_RESPREAD = 3

# ── Difficulty ───────────────────────────────────────────────
DIFF_BULLETS = {0: 30, 1: 50, 2: 100, 3: 200}  # C: DAT_00406da8

# ── RNG (FUN_00402000) ─────────────────────────────────────
LCG_MULT = 0x343FD
LCG_ADD = 0x269EC3
LCG_MASK = 0x7FFF

# ── Bullet Constants ─────────────────────────────────────────
INACTIVE = 0xFF          # C: angle_index == 0xff
TYPE_NORMAL = 0
TYPE_HOMING = 1
TYPE_H_ACCEL = 2
TYPE_ACCEL = 3

# Type 2 (H-Accel) limits
VX_CAP = 96              # C: vx < 0x60
VY_CAP = 96
MAX_BOUNCE = 4           # C: if (DAT_00406dac < 4)

# Homing steering (C: Stage2_GameEntityLoop)
STEER_NEAR = 0x19        # C: diff < 25 → steer +1 toward target
STEER_LOSE = 0x28        # C: diff < 40 → lose lock (type→0); else steer -1

# Homing counter phase jitter (C: counter = RNG & 7 after re-aim)
HOMING_PHASE_MASK = 0x7

# Pixel conversion
RAW_SHIFT = 6            # C: raw >> 6
PIXEL_OFFSET = 4         # C: (raw >> 6) - 4

# Velocity tables
VEL_TABLE_ADDR = 0x00405d74   # 64 entries × 12 bytes (3 i32s each)
ACCEL_TABLE_ADDR = 0x00406074
NUM_ANGLES = 64
OCTANT_SEARCH = 7             # C: do { ... } while (iVar2 < 7)


# ── Frame rate (verified from assembly: G_ScoreMultiplier=16 → 1000/16=62.5fps) ──
FPS = 62

# Derived timing (frames at current FPS)
SPAWN_INTERVAL = int(SPAWN_INTERVAL_MS * FPS / 1000)    # 240f
PATTERN_CHECK = int(PATTERN_CHECK_MS * FPS / 1000)       # 400f
PATTERN_ACTIVE = int(PATTERN_ACTIVE_MS * FPS / 1000)     # 800f
GRAZE_WINDOW = int(GRAZE_CHAIN_MS * FPS / 1000)          # 80f
