"""
simulator/jit_core.py — Numba-JIT accelerated core functions.

These replace the pure-Python hot-path functions in functions.py, bullet.py,
and engine.py with @njit equivalents for ~10-50x speedup on inner loops.
All functions are stateless — take values, return values.
"""
import numpy as np
from numba import njit

# ── Import config constants as plain values for @njit ────────
# (numba can't read from Python module attrs at JIT time, so hardcode)
LCG_MULT = 0x343FD
LCG_ADD = 0x269EC3
LCG_MASK = 0x7FFF

RAW_SHIFT = 6
PIXEL_OFFSET = 4
NUM_ANGLES = 64

HIT_X1, HIT_X2 = 2, 13
HIT_Y1, HIT_Y2 = 0, 10
GRAZE_DX_OFFSET = 4
GRAZE_DX_LIMIT = 23   # C: dx+4 < 0x17
GRAZE_DY_OFFSET = 6
GRAZE_DY_LIMIT = 20   # C: dy+6 < 0x14

PLAYER_CENTER = 6
STEER_NEAR = 0x19
STEER_LOSE = 0x28
HOMING_PHASE_MASK = 0x7

VX_CAP = 96
VY_CAP = 96

SAFETY_MARGIN = 2.0
COLLISION_VAL = 1e8

# ── RNG ──────────────────────────────────────────────────────
@njit
def rng_next(state):
    """FUN_00402000: LCG step. Returns (new_state, value)."""
    state = (state * LCG_MULT + LCG_ADD) & 0xFFFFFFFF
    return state, (state >> 16) & LCG_MASK


# ── Pixel conversion ────────────────────────────────────────
@njit
def raw_to_pixel(raw):
    """Convert raw internal coord to screen pixel."""
    return (raw >> RAW_SHIFT) - PIXEL_OFFSET


# ── Velocity table lookup ───────────────────────────────────
@njit
def lookup_vel(angle_idx, vel_table):
    """VEL_TABLE access: 64 entries × 2 i32s (vx, vy)."""
    idx = (angle_idx & (NUM_ANGLES - 1)) * 2
    return vel_table[idx], vel_table[idx + 1]


# ── Collision + graze check (combined, single pass) ─────────
@njit
def check_collision_graze(b_raw_x, b_raw_y, px, py):
    """
    Combined collision and graze check for one bullet.
    Returns (is_collision, in_graze_zone).
    Exact match to C: Stage2_GameEntityLoop.c
    """
    bpx = raw_to_pixel(b_raw_x)
    bpy = raw_to_pixel(b_raw_y)
    dx = bpx - px
    dy = bpy - py

    # Graze proximity (C: dx+4 < 0x17 AND dy+6 < 0x14)
    in_graze = (dx + GRAZE_DX_OFFSET < GRAZE_DX_LIMIT
                and dy + GRAZE_DY_OFFSET < GRAZE_DY_LIMIT)

    # Collision (C: dx-2 < 0xb AND dy < 10)
    collision = (dx >= HIT_X1 and dx < HIT_X2
                 and dy >= HIT_Y1 and dy < HIT_Y2)

    return collision, in_graze


# ── Bullet movement (per type, pure functions) ───────────────
@njit
def move_type0(raw_x, raw_y, angle_idx, vel_table):
    """Type 0 (Normal): constant velocity from VEL_TABLE."""
    vx, vy = lookup_vel(angle_idx, vel_table)
    return raw_x + vx, raw_y + vy


@njit
def move_type3(raw_x, raw_y, angle_idx, accel_table):
    """Type 3 (Accelerating): velocity from ACCEL_TABLE."""
    idx = (angle_idx & (NUM_ANGLES - 1)) * 2
    vx = accel_table[idx]
    vy = accel_table[idx + 1]
    return raw_x + vx, raw_y + vy


@njit
def move_type2_haccel(raw_x, raw_y, vx, vy, player_px, player_py):
    """
    Type 2 (H-Accel): accelerate toward player, capped velocity.
    Returns (new_raw_x, new_raw_y, new_vx, new_vy).
    """
    bx = raw_to_pixel(raw_x)
    by = raw_to_pixel(raw_y)
    tx = player_px + PLAYER_CENTER
    ty = player_py + PLAYER_CENTER

    if bx < tx:
        if vx < VX_CAP:
            vx += 1
    elif vx > -VX_CAP:
        vx -= 1

    if by < ty:
        if vy < VY_CAP:
            vy += 1
    elif vy > -VY_CAP:
        vy -= 1

    return raw_x + vx, raw_y + vy, vx, vy


@njit
def move_type1_homing(raw_x, raw_y, angle_idx, counter, timer,
                      vel_table, rng_state, player_px, player_py,
                      vel_table_full):
    """
    Type 1 (Homing): counter-based re-targeting with steering.
    vel_table_full: flat array of (vx, vy, tan_ratio) × 64 entries (3 i32s each).
    Returns (new_raw_x, new_raw_y, new_angle_idx, new_counter, new_rng_state).
    """
    counter += 1

    if counter >= timer:
        # Re-aim: RNG phase jitter
        rng_state, rv = rng_next(rng_state)
        counter = rv & HOMING_PHASE_MASK

        # Compute aimed angle (inline — avoids function call overhead)
        # dx = (player_x+6) - (raw_x>>6), dy = (player_y+6) - (raw_y>>6)
        dx = (player_px + PLAYER_CENTER) - (raw_x >> RAW_SHIFT)
        dy = (player_py + PLAYER_CENTER) - (raw_y >> RAW_SHIFT)

        # Octant determination (assembly-verified from FUN_00402d68)
        if dx < 0:
            if dy <= 0:
                if dy < dx:
                    octant, divisor = 0x20, dy
                else:
                    octant, divisor = 0x28, dy
            else:
                if dx < -dy:
                    octant, divisor = 0x18, dy
                else:
                    octant, divisor = 0x10, dy
        elif dy < 0:
            if dx < -dy:
                octant, divisor = 0x30, dy
            else:
                octant, divisor = 0x38, dy
        else:
            if dx == 0:
                octant, divisor = 0x10, 0
            elif dy == 0:
                octant, divisor = 0, 0
            elif dx < dy:
                octant, divisor = 8, dy
            else:
                octant, divisor = 0, dy

        # Octant search — EXACT assembly match (FUN_00402d68):
        # quotient = abs(dx * 0x400 / divisor)
        # minimize abs(quotient - tan_ratio) across 7 candidates
        target = octant
        if divisor != 0:
            quotient = abs(dx * 0x400) // abs(divisor)
            best_diff = 0x10000
            entry_idx = octant & 0xFF
            target = octant & 0xFF
            for s in range(7):
                idx3 = ((entry_idx + s) % NUM_ANGLES) * 3
                vy = vel_table_full[idx3 + 1]
                tan_ratio = vel_table_full[idx3 + 2]
                if vy == 0:
                    diff = 0xFFFF
                elif quotient <= tan_ratio:
                    diff = tan_ratio - quotient
                else:
                    diff = quotient - tan_ratio
                if diff >= best_diff:
                    break
                best_diff = diff
                target = (octant + s + 1) & 0xFF

        # Spread: (angle + RNG%spread + 1 - spread/2) & 0x3F
        rng_state, rv = rng_next(rng_state)
        spread_val = 3  # HOMING_RESPREAD
        target = (target + (rv % spread_val) + 1 - (spread_val // 2)) & 0x3F

        # Steering logic
        cur = angle_idx
        if target != cur:
            if target < cur:
                cur = (cur - NUM_ANGLES) & 0xFF
            diff = (target - cur) & 0xFF
            if diff < STEER_NEAR:
                angle_idx = (angle_idx + 1) & (NUM_ANGLES - 1)
            elif diff < STEER_LOSE:
                # Lose lock: revert to Type 0 behavior
                vx, vy = lookup_vel(angle_idx, vel_table)
                return raw_x + vx, raw_y + vy, angle_idx, counter, rng_state, 0
            else:
                angle_idx = (angle_idx - 1) & (NUM_ANGLES - 1)

    # Movement
    vx, vy = lookup_vel(angle_idx, vel_table)
    return raw_x + vx, raw_y + vy, angle_idx, counter, rng_state, 1


# ── Danger scoring (for AI use) ──────────────────────────────
@njit
def score_pos_danger(px, py, bullets_arr):
    """
    Inverse-square danger scoring for a position against bullet array.
    bullets_arr: (N, 2) array of (bx, by) positions.
    Returns (danger_score, is_fatal).
    """
    B = bullets_arr.shape[0]
    danger = 0.0
    for i in range(B):
        dx = bullets_arr[i, 0] - px
        dy = bullets_arr[i, 1] - py
        if (dx >= HIT_X1 - SAFETY_MARGIN and dx < HIT_X2 + SAFETY_MARGIN
                and dy >= HIT_Y1 - SAFETY_MARGIN and dy < HIT_Y2 + SAFETY_MARGIN):
            return COLLISION_VAL, True
        d2 = dx * dx + dy * dy
        if d2 < 4.0:
            d2 = 4.0
        danger += 2000.0 / d2
    return danger, False
