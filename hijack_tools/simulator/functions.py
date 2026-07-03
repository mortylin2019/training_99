"""
simulator/functions.py — Pure Python equivalents of every C function in 99.exe.

Each function matches its C counterpart exactly:
- Same inputs → same outputs
- Same global state mutations
- No side effects beyond documented globals

Used as the verified reference implementation for the simulator.
All functions are stateless — globals passed as parameters.
"""
import math
from .config import *

# ═══════════════════════════════════════════════════════════════
# FUN_00402000 — LCG Random Number Generator
# ═══════════════════════════════════════════════════════════════

def rng_next(state):
    """FUN_00402000: LCG step. Returns (new_state, random_value)."""
    state = (state * LCG_MULT + LCG_ADD) & 0xFFFFFFFF
    return state, (state >> 16) & LCG_MASK


# ═══════════════════════════════════════════════════════════════
# FUN_00402d68 — Compute aimed angle index toward player
# ═══════════════════════════════════════════════════════════════

def compute_aimed_angle(bullet_raw_x, bullet_raw_y, player_px, player_py,
                        rng_state, spread):
    """
    FUN_00402d68 — EXACT assembly-equivalent (register-verified from binary).

    Assembly trace:
      ecx=dx, esi=dy
      bl=octant_base (0,8,0x10,0x18,0x20,0x28,0x30,0x38)
      Octant search with tan_ratio from VEL_TABLE_FULL
      inc ebx after each improvement → off-by-one in final angle
      Spread: (angle + RNG%spread + 1 - spread/2) & 0x3F

    Returns: (new_rng_state, angle_index_0_63)
    """
    from .tables import VEL_TABLE_FULL

    # dx = (player_x+6) - (bullet_raw_x>>6)
    # dy = (player_y+6) - (bullet_raw_y>>6)
    dx = (player_px + PLAYER_CENTER) - ((bullet_raw_x & 0xFFFFFFFF) >> RAW_SHIFT)
    dy = (player_py + PLAYER_CENTER) - ((bullet_raw_y & 0xFFFFFFFF) >> RAW_SHIFT)

    # Octant determination (exact assembly branches)
    # esi=dy, ecx=dx. Binary always uses idiv esi → divisor is always dy.
    if dx < 0:
        if dy <= 0:
            octant = 0x20 if dy < dx else 0x28
        else:
            octant = 0x18 if dx < -dy else 0x10
    elif dy < 0:
        octant = 0x30 if dx < -dy else 0x38
    else:
        if dx == 0:    octant = 0x10
        elif dy == 0:  octant = 0
        elif dx < dy:  octant = 8   # asm: cmp esi,ecx; jle → dy<=dx→0, else→8
        else:          octant = 0

    # Binary: if dy == 0 → skip search (angle = octant); else divisor = dy
    if dy == 0:
        angle = octant & 0xFF
    else:
        # idiv: (dx*0x400) / dy → abs result
        quotient = abs(dx * 0x400) // abs(dy)  # abs avoids sign mismatch: idiv truncates, // floors

        # Search loop (esi=counter, ebx=angle, edx=table_ptr)
        best_diff = 0x10000
        entry_idx = octant & 0xFF
        angle = octant & 0xFF
        counter = 0

        while counter < OCTANT_SEARCH:
            vx, vy, tan_ratio = VEL_TABLE_FULL[entry_idx % NUM_ANGLES]

            if vy == 0:
                diff = 0xFFFF   # worst score
            else:
                # abs(quotient - tan_ratio)
                if quotient <= tan_ratio:
                    diff = tan_ratio - quotient
                else:
                    diff = quotient - tan_ratio

            # jge → break if diff >= best_diff
            if diff >= best_diff:
                break

            best_diff = diff
            entry_idx += 1
            angle = (octant + counter + 1) & 0xFF  # inc ebx equivalent
            counter += 1

    # Spread jitter (assembly: idiv [esp], add bl + RNG%spread + 1 - spread/2)
    if spread:
        rng_state, rv = rng_next(rng_state)
        angle = (angle + (rv % spread) + 1 - (spread >> 1)) & 0x3F

    return rng_state, angle & 0x3F


# ═══════════════════════════════════════════════════════════════
# FUN_00402e88 — Spawn one bullet into a slot
# ═══════════════════════════════════════════════════════════════

def spawn_bullet(slot_raw_x, slot_raw_y, slot_fields,
                 player_px, player_py,
                 pattern, bounce_limit,
                 rng_state):
    """
    FUN_00402e88(void) — spawns bullet at current entity slot pointer.

    Sets: raw_x, raw_y, angle_index, type, timer, counter, grazed, vx, vy.

    Args:
        slot_raw_x, slot_raw_y: output — mutated in place
        slot_fields: dict with keys type, timer, counter, grazed, vx, vy, angle_index
        player_px, player_py: player position
        pattern: active pattern (0-7)
        bounce_limit: current Type 2 count
        rng_state: current LCG state

    Returns:
        (new_rng_state, new_bounce_limit, slot_fields_updated)
    """
    # Pick random edge (0-3)
    rng_state, rv = rng_next(rng_state)
    edge = rv & 3

    if edge == 0:    # Top
        rng_state, rv = rng_next(rng_state)
        slot_raw_x = rv % RAW_MAX_X
        slot_raw_y = 0
    elif edge == 1:  # Bottom
        rng_state, rv = rng_next(rng_state)
        slot_raw_x = rv % RAW_MAX_X
        slot_raw_y = RAW_MAX_Y
    elif edge == 2:  # Left
        slot_raw_x = 0
        rng_state, rv = rng_next(rng_state)
        slot_raw_y = rv % RAW_MAX_Y
    else:            # Right
        slot_raw_x = RAW_MAX_X
        rng_state, rv = rng_next(rng_state)
        slot_raw_y = rv % RAW_MAX_Y

    info = PATTERN_INFO.get(pattern, PATTERN_INFO[0])
    slot_fields["type"] = info["type"]
    slot_fields["timer"] = info["timer"]
    slot_fields["counter"] = 0
    slot_fields["grazed"] = 0
    slot_fields["vx"] = 0
    slot_fields["vy"] = 0

    # Pattern 5: random homing timer
    if pattern == 5:
        rng_state, rv = rng_next(rng_state)
        slot_fields["timer"] = ((rv & 3) + 1) * 16

    # Pattern 7: H-Accel (no aiming)
    if pattern == 7:
        if bounce_limit >= MAX_BOUNCE:
            slot_fields["type"] = TYPE_NORMAL
        else:
            bounce_limit += 1
        slot_fields["angle_index"] = 0
        return rng_state, bounce_limit, slot_raw_x, slot_raw_y, slot_fields

    # Aimed spawn
    spread = info.get("spread", 5)
    rng_state, angle = compute_aimed_angle(
        slot_raw_x, slot_raw_y, player_px, player_py, rng_state, spread)
    slot_fields["angle_index"] = angle

    return rng_state, bounce_limit, slot_raw_x, slot_raw_y, slot_fields


# ═══════════════════════════════════════════════════════════════
# Bullet movement — per-type (from FUN_00402fbc)
# ═══════════════════════════════════════════════════════════════

def move_bullet_type0(raw_x, raw_y, angle_index):
    """Type 0 (Normal): constant velocity from VEL_TABLE."""
    from .tables import VEL_TABLE
    idx = angle_index & (NUM_ANGLES - 1)
    vx, vy = VEL_TABLE[idx]
    return raw_x + vx, raw_y + vy


def move_bullet_type1(raw_x, raw_y, angle_index, btype, timer, counter,
                      player_px, player_py, rng_state):
    """
    Type 1 (Homing): timer-based re-aim with gradual steering.
    Returns (raw_x, raw_y, angle_index, btype, counter, rng_state).
    """
    from .tables import VEL_TABLE

    counter += 1
    if counter >= timer:
        # Re-aim: counter = RNG & 7 (phase jitter, NOT zero)
        rng_state, rv = rng_next(rng_state)
        counter = rv & HOMING_PHASE_MASK

        # Compute target angle (FUN_00402d68 with spread=3)
        rng_state, target = compute_aimed_angle(
            raw_x, raw_y, player_px, player_py, rng_state, HOMING_RESPREAD)

        cur = angle_index
        if target != cur:
            if target < cur:
                cur = (cur - 0x40) & 0xFF
            diff = (target - cur) & 0xFF
            if diff < STEER_NEAR:       # < 25: steer +1
                angle_index = (angle_index + 1) & (NUM_ANGLES - 1)
            elif diff < STEER_LOSE:     # < 40: lose lock → Normal
                btype = TYPE_NORMAL
            else:                        # >= 40: steer -1
                angle_index = (angle_index - 1) & (NUM_ANGLES - 1)

    idx = angle_index & (NUM_ANGLES - 1)
    vx, vy = VEL_TABLE[idx]
    return raw_x + vx, raw_y + vy, angle_index, btype, counter, rng_state


def move_bullet_type2(raw_x, raw_y, vx, vy,
                      player_px, player_py):
    """
    Type 2 (Homing-Accel): accelerate toward player+6, capped at ±96.
    Returns (raw_x, raw_y, vx, vy).
    """
    bx = (raw_x >> RAW_SHIFT) - PIXEL_OFFSET
    by = (raw_y >> RAW_SHIFT) - PIXEL_OFFSET
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


def move_bullet_type3(raw_x, raw_y, angle_index):
    """Type 3 (Accelerating): velocity from ACCEL_TABLE."""
    from .tables import ACCEL_TABLE
    idx = angle_index & (NUM_ANGLES - 1)
    vx, vy = ACCEL_TABLE[idx]
    return raw_x + vx, raw_y + vy


def is_offscreen(raw_x, raw_y):
    """C: unsigned comparison — negative raw coords wrapped to 32-bit catch left/top edge exits."""
    return (raw_x & 0xFFFFFFFF) >= RAW_MAX_X or (raw_y & 0xFFFFFFFF) >= RAW_MAX_Y


# ═══════════════════════════════════════════════════════════════
# Collision & Graze (from FUN_00402fbc)
# ═══════════════════════════════════════════════════════════════

def pixel_from_raw(raw):
    """C: (raw >> 6) - 4."""
    return ((raw & 0xFFFFFFFF) >> RAW_SHIFT) - PIXEL_OFFSET


def check_collision(bullet_raw_x, bullet_raw_y, player_px, player_py):
    """
    C: if (dx-2 < 0xb && dy < 10) → hit.
    Returns True if bullet hits player.
    """
    bx = pixel_from_raw(bullet_raw_x)
    by = pixel_from_raw(bullet_raw_y)
    dx = bx - player_px
    dy = by - player_py
    return (dx - HIT_X1 >= 0 and dx < HIT_X2
            and dy >= HIT_Y1 and dy < HIT_Y2)


def check_graze_enter(bullet_raw_x, bullet_raw_y, player_px, player_py):
    """
    C: if (dx+4 < 0x17 && dy+6 < 0x14) → in graze zone.
    Returns True if bullet is in graze proximity of player.
    """
    bx = pixel_from_raw(bullet_raw_x)
    by = pixel_from_raw(bullet_raw_y)
    dx = bx - player_px
    dy = by - player_py
    return dx + 4 < GRAZE_DX and dy + 6 < GRAZE_DY


# ═══════════════════════════════════════════════════════════════
# Pattern system state machine (from FUN_00402fbc)
# ═══════════════════════════════════════════════════════════════

def pattern_update(frame, next_pattern_time, pattern, rng_state):
    """
    C pattern check (at entity loop boundary).
    Returns (new_pattern, new_next_pattern_time, rng_state).
    """
    if frame < next_pattern_time:
        return pattern, next_pattern_time, rng_state

    if pattern == 0:
        rng_state, rv = rng_next(rng_state)
        if rv < PATTERN_CHANCE:
            pattern = (rv % 7) + 1
            next_pattern_time = frame + PATTERN_ACTIVE
        else:
            next_pattern_time = frame + PATTERN_CHECK
    else:
        pattern = 0
        next_pattern_time = frame + PATTERN_CHECK

    return pattern, next_pattern_time, rng_state


# ═══════════════════════════════════════════════════════════════
# Player movement (from FUN_00403400)
# ═══════════════════════════════════════════════════════════════

def move_player(px, py, input_bits):
    """
    C: reads G_InputState bitmask, moves 1px/frame in each active direction.
    Returns (new_px, new_py).
    """
    dx = (1 if input_bits & 8 else 0) - (1 if input_bits & 1 else 0)
    dy = (1 if input_bits & 4 else 0) - (1 if input_bits & 2 else 0)
    px = max(0, min(SCR_W, px + dx))
    py = max(0, min(SCR_H, py + dy))
    return px, py


# ═══════════════════════════════════════════════════════════════
# Frame step (one entity loop iteration — single bullet)
# ═══════════════════════════════════════════════════════════════

def process_one_bullet(bullet, player_px, player_py, dead, rng_state,
                       active_near, graze_total,
                       graze_chain, graze_chain_time, frame):
    """
    Process ONE bullet in the entity loop (one iteration of FUN_00402fbc).
    Returns updated state for this bullet + global counters.

    This is a PURE function — all state passed in/out explicitly.
    """
    from .tables import VEL_TABLE, ACCEL_TABLE

    raw_x = bullet["raw_x"]
    raw_y = bullet["raw_y"]
    angle_index = bullet["angle_index"]
    btype = bullet["type"]
    timer = bullet["timer"]
    counter = bullet["counter"]
    grazed = bullet["grazed"]
    vx = bullet["vx"]
    vy = bullet["vy"]

    # Off-screen check
    if is_offscreen(raw_x, raw_y):
        if btype & 2:  # type 2 (H-Accel) or 3 (Accel) — asm: test [ecx+0xa],2
            bounce_delta = -1
        else:
            bounce_delta = 0
        return {"action": "respawn", "bounce_delta": bounce_delta,
                "rng_state": rng_state}

    # Movement
    if btype == TYPE_HOMING:
        raw_x, raw_y, angle_index, btype, counter, rng_state = \
            move_bullet_type1(raw_x, raw_y, angle_index, btype,
                              timer, counter, player_px, player_py, rng_state)
    elif btype == TYPE_H_ACCEL:
        raw_x, raw_y, vx, vy = move_bullet_type2(
            raw_x, raw_y, vx, vy, player_px, player_py)
    elif btype == TYPE_ACCEL:
        raw_x, raw_y = move_bullet_type3(raw_x, raw_y, angle_index)
    else:  # TYPE_NORMAL
        raw_x, raw_y = move_bullet_type0(raw_x, raw_y, angle_index)

    # Collision + graze (skip if already dead)
    hit = False
    if not dead:
        if check_collision(raw_x, raw_y, player_px, player_py):
            hit = True

        in_graze = check_graze_enter(raw_x, raw_y, player_px, player_py)
        if in_graze and not grazed:
            grazed = 1
            active_near += 1
        elif not in_graze and grazed:
            grazed = 0
            active_near -= 1
            if active_near > 0:
                graze_total += active_near
                if frame < graze_chain_time:
                    if graze_chain < GRAZE_CHAIN_MAX:
                        graze_chain += 1
                else:
                    graze_chain = 1
                graze_chain_time = frame + GRAZE_WINDOW

    bullet_out = {
        "raw_x": raw_x, "raw_y": raw_y,
        "angle_index": angle_index, "type": btype,
        "timer": timer, "counter": counter,
        "grazed": grazed, "vx": vx, "vy": vy,
    }
    return {
        "action": "processed",
        "bullet": bullet_out,
        "hit": hit,
        "active_near": active_near,
        "graze_total": graze_total,
        "graze_chain": graze_chain,
        "graze_chain_time": graze_chain_time,
        "rng_state": rng_state,
    }
