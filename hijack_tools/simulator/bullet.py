"""
simulator/bullet.py - Bullet struct + per-type movement.

Matches Stage2_GameEntityLoop.c (FUN_00402fbc) exactly.
Entity struct: 15 bytes at 0x00406e10.
"""
from dataclasses import dataclass
import math
from .config import *
from .tables import VEL_TABLE, ACCEL_TABLE


@dataclass
class Bullet:
    """Matches 15-byte entity at 0x00406e10."""
    raw_x: int = 0          # offset 0x00
    raw_y: int = 0          # offset 0x04
    angle_index: int = 0    # offset 0x08, 0xFF = inactive
    grazed: int = 0         # offset 0x09
    type: int = 0           # offset 0x0A: 0=Normal,1=Homing,2=H-Accel,3=Accel
    timer: int = 0          # offset 0x0B (homing re-target interval)
    counter: int = 0        # offset 0x0C (internal counter for Type 1)
    vx: int = 0             # offset 0x0D (signed, for Type 2)
    vy: int = 0             # offset 0x0E

    @property
    def x(self): return (self.raw_x >> RAW_SHIFT) - PIXEL_OFFSET
    @property
    def y(self): return (self.raw_y >> RAW_SHIFT) - PIXEL_OFFSET


def move_bullet(b: Bullet, player_x: int, player_y: int, rng):
    """
    Move one bullet matching FUN_00402fbc type-specific branches.
    Modifies bullet in-place.
    rng: LCG instance (FUN_00402000) for homing phase jitter.
    """
    if b.type == TYPE_HOMING:
        # Type 1: Homing (C: cVar1 == '\x01')
        b.counter += 1
        if b.counter >= b.timer:
            # Re-aim: FUN_00402d68(ECX, 3) with spread=HOMING_RESPREAD
            # C: counter = RNG & 7 (phase jitter), NOT counter = 0
            b.counter = rng.next() & HOMING_PHASE_MASK

            # Assembly-verified octant search for homing re-target (spread=3)
            from .functions import compute_aimed_angle
            rng_state = rng.state
            rng_state, target = compute_aimed_angle(
                b.raw_x, b.raw_y, player_x, player_y, rng_state, HOMING_RESPREAD)
            rng.state = rng_state

            cur = b.angle_index
            if target != cur:
                if target < cur:
                    cur = (cur - 0x40) & 0xFF
                diff = (target - cur) & 0xFF
                if diff < STEER_NEAR:       # < 25: steer +1 toward target
                    b.angle_index = (b.angle_index + 1) & (NUM_ANGLES - 1)
                elif diff < STEER_LOSE:     # < 40: lost lock → fall back to Normal
                    b.type = TYPE_NORMAL
                else:                        # >= 40: steer -1 toward target
                    b.angle_index = (b.angle_index - 1) & (NUM_ANGLES - 1)

        # Movement (C: LAB_0040326e — velocity table lookup)
        idx = b.angle_index & (NUM_ANGLES - 1)
        vx, vy = VEL_TABLE[idx]
        b.raw_x += vx
        b.raw_y += vy

    elif b.type == TYPE_H_ACCEL:
        # Type 2: Homing-Acceleration (C: cVar1 == '\x02')
        # Compare pixel positions (C: iVar11 vs DAT_00406d6c+6)
        bx = b.x
        by = b.y
        tx = player_x + PLAYER_CENTER
        ty = player_y + PLAYER_CENTER

        if bx < tx:
            if b.vx < VX_CAP:
                b.vx += 1
        elif b.vx > -VX_CAP:
            b.vx -= 1

        if by < ty:
            if b.vy < VY_CAP:
                b.vy += 1
        elif b.vy > -VY_CAP:
            b.vy -= 1

        b.raw_x += b.vx
        b.raw_y += b.vy

    elif b.type == TYPE_ACCEL:
        # Type 3: Accelerating (C: cVar1 == '\x03')
        # Uses ACCEL_TABLE at 0x00406074 (64 entries × 12 bytes)
        idx = b.angle_index & (NUM_ANGLES - 1)
        vx, vy = ACCEL_TABLE[idx]
        b.raw_x += vx
        b.raw_y += vy

    else:
        # Type 0: Normal (C: falls through to LAB_0040326e)
        idx = b.angle_index & (NUM_ANGLES - 1)
        vx, vy = VEL_TABLE[idx]
        b.raw_x += vx
        b.raw_y += vy
