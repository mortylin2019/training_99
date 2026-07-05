# Entity Management and Logic

## Overview
Based on `Stage2_GameEntityLoop.c` and `Bullet_Mechanics.c`. The game uses a fixed array of 300 entity structures at `0x00406e10`.

## Entity Array Logic
- **Fixed Size**: 300 slots, each 15 bytes (0x0F). Iterated as `ptr += 0x0F`.
- **Active Limit**: `G_CurrentBulletCount` controls the loop boundary — entities beyond this index are not processed. This count starts at the difficulty level (30/50/100/200) and only increases when new bullets spawn.
- **Recycle on Death**: 
  - When an entity goes out of bounds (raw_x ≥ 0x5101 or raw_y ≥ 0x3D01), the game calls `Entity_SpawnBullet()` to re-initialize the slot in-place.
  - There is no explicit removal — slots are recycled immediately.
  - `G_CurrentBulletCount` never decreases during gameplay; it only increments via the spawn timer.

## Type 2 (Pattern 7 — Homing Acceleration)
- Counter `DAT_00406dac` (at `0x00406dac`) limits Type 2 bullets to 4 on screen.
- When a Type 2 bullet goes out of bounds: decrements `DAT_00406dac`, recycles the slot.
- Pattern 7 stops spawning Type 2 once the limit is hit.

## Spawning Logic
- `Entity_SpawnBullet`: initializes slot with edge position + type/angle from active pattern
- Types are determined by `G_NextBulletPattern`, NOT random per bullet:
  - Pattern 0: Type 0 (Normal), random angle
  - Pattern 1: Type 0 (Normal)
  - Pattern 2–5: Type 1 (Homing), varying timers
  - Pattern 6: Type 3 (Accelerating)
  - Pattern 7: Type 2 (Homing-Accel), max 4
