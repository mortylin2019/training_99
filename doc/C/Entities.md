# Entities: Mechanics

## Overview
Bullet types, behavior, and spawning logic.

## Bullet Types

1. **Type 0 (Normal)**
   - Constant velocity from lookup table `DAT_00405d74`
   - 64 angles × 12 bytes (vx:i32, vy:i32, ?:i32)
   - Movement: `raw_x += vx_raw`, `raw_y += vy_raw`

2. **Type 1 (Homing)**
   - Uses same velocity table as Type 0
   - Has timer-based angle recalculation (every 16/32/48/64 frames depending on pattern)
   - `FUN_00402d68` calculates target angle toward player
   - Steers ±1 toward target per update
   - Falls back to Type 0 if angular gap too large

3. **Type 2 (Homing Acceleration — NOT bounce!)**
   - Accelerates toward player (PlayerX+6, PlayerY+6)
   - vx/vy stored as signed bytes at offsets 0x0D/0x0E
   - ±1 per frame acceleration, capped at ±96 (0x60)
   - Max 4 on screen (counter at `0x00406dac`)

4. **Type 3 (Accelerating)**
   - Uses acceleration table `DAT_00406074` (64 angles × 12 bytes)
   - Higher velocity values than Type 0 table
   - Pattern 6 spawns these

## Spawning
- `Entity_SpawnBullet`: initializes a free slot (angle_index=0xFF) in `G_EntityArray`
- Position: random on one of 4 edges (top/bottom/left/right)
- Initial type/angle set based on active pattern (`G_NextBulletPattern`)
- Bullet that goes off-screen: respawned immediately

## Player
- Player position `G_PlayerX`, `G_PlayerY` updated from `G_InputState` bitmask
- Hitbox: 11px wide × 10px tall (2 ≤ bx-px < 13, 0 ≤ by-py < 10)
- Movement: 1 px/frame per axis, diagonals not normalized
