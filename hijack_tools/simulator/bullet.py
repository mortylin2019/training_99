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
    Uses @njit-accelerated functions from jit_core for hot paths.
    Modifies bullet in-place.
    rng: LCG instance (FUN_00402000) for homing phase jitter.
    """
    from .jit_core import (move_type0, move_type3, move_type2_haccel,
                           move_type1_homing)
    from .tables import VEL_TABLE_FLAT, ACCEL_TABLE_FLAT, VEL_TABLE_FULL_FLAT

    if b.type == TYPE_HOMING:
        # Type 1: Homing — delegate to @njit function
        new_raw_x, new_raw_y, new_angle, new_counter, new_rng_state = \
            move_type1_homing(
                b.raw_x, b.raw_y, b.angle_index, b.counter, b.timer,
                VEL_TABLE_FLAT, rng.state,
                int(player_x), int(player_y),
                VEL_TABLE_FULL_FLAT)
        b.raw_x = new_raw_x
        b.raw_y = new_raw_y
        b.angle_index = new_angle
        b.counter = new_counter
        rng.state = new_rng_state

    elif b.type == TYPE_H_ACCEL:
        # Type 2: Homing-Acceleration
        b.raw_x, b.raw_y, b.vx, b.vy = move_type2_haccel(
            b.raw_x, b.raw_y, b.vx, b.vy,
            int(player_x), int(player_y))

    elif b.type == TYPE_ACCEL:
        # Type 3: Accelerating
        b.raw_x, b.raw_y = move_type3(
            b.raw_x, b.raw_y, b.angle_index, ACCEL_TABLE_FLAT)

    else:
        # Type 0: Normal
        b.raw_x, b.raw_y = move_type0(
            b.raw_x, b.raw_y, b.angle_index, VEL_TABLE_FLAT)
