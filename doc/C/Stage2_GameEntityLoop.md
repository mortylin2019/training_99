# Stage 2: Entity Loop / Game Logic

## Overview
This file (`Game_EntityLoop`) contains the core game logic for the PLAYING state, plus the render wrapper (`FUN_00403400`).

## Logic Breakdown

1. **Bullet Updates**:
   - Iterates through the 300-slot entity array (15 bytes each)
   - For each active bullet (angle_index ≠ 0xFF):
     - **Type 0**: `raw += velocity_table[angle]` (constant)
     - **Type 1**: Increments internal counter; when counter == timer, recalculates angle toward player via `FUN_00402d68`, adjusts ±1
     - **Type 2**: Accelerates toward player (PlayerX+6, PlayerY+6), vx/vy capped at ±96
     - **Type 3**: `raw += accel_table[angle]`
   - Off-screen bullets (raw_x ≥ 0x5101 or raw_y ≥ 0x3D01) are respawned immediately
   - Bullets rendered as 4×4 pixel blocks into DIB section `ppvBits_004069fc`

2. **Collision Detection**:
   - Hitbox: `2 ≤ (bx−px) < 13` AND `0 ≤ (by−py) < 10` (11×10 px)
   - On hit: sets `G_DeathTime`, sets `G_GameOverFlag = 1`
   - Death animation: GameOverFlag increments 1→0x11 over successive frames

3. **Graze System**:
   - Proximity zone: `(bx−px+4 < 23) AND (by−py+6 < 20)`
   - When bullet enters zone: `G_ActiveEntityCount++`
   - When bullet leaves zone: `G_ActiveEntityCount−−`, and **`G_TotalEntitiesSpawned += G_ActiveEntityCount`**
   - Graze chain: `G_PatternCounter` (1–10), resets after 1000ms

4. **Spawning Logic**:
   - Triggers when `G_CurrentBulletCount ≤ slot_index` AND spawn timer expired
   - Spawn interval: 3000ms
   - Max bullets: 299 (or pattern 7 limit)
   - `G_CurrentBulletCount` starts at difficulty level and only increments on spawn

5. **Pattern System**:
- 37.5% chance (0x3000/0x8000) every 5s to start a pattern
- Patterns last 10s (10000ms timer), then cooldown 5s. G_PatternDuration=100 is display-only.
   - Pattern bar displayed at top of screen via `BitBlt`

6. **Player Movement** (in `FUN_00403400`):
   - Reads `G_InputState` bitmask, moves player 1px/frame
   - Clamped to [0, 0x130] × [0, 0xE0]
   - Player rendered as 16×16 pixel block at current position

## Key Variables
- `G_EntityArray` (`0x00406e10`): 300×15 byte bullet array
- `G_ActiveEntityCount` (`0x00406db4`): bullets in graze proximity
- `G_TotalEntitiesSpawned` (`0x00406db8`): accumulated graze score
- `G_PatternCounter` (`0x00406df0`): graze chain counter (1–10)
- `G_NextBulletPattern` (`0x00406dbc`): active pattern ID (0–7)
- `G_PatternDuration` (`0x00406db0`): remaining pattern frames
