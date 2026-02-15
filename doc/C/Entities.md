# Entities: Mechanics

## Overview
Bullet logic and types.

## Bullet Types
1. **Type 1 (Homing)**
   - `Entity_Type1_Homing.c`
   - Uses lookup tables `DAT_00405d74`, `DAT_00405d78`.
   - Adjusts velocity to track player with some inertia.

2. **Type 2 (Bounce)**
   - `Entity_Type2_Bounce.c`
   - Simple reflection logic off screen types.

3. **Type 3 (Accelerating)**
   - Uses `uVar15` from `Util_Random`.
   - Often moves straight but increases speed over time.

## Spawning
- `Entity_SpawnBullet`: Finds a free slot in `G_EntityArray`.
- Initializes position (Edge of screen usually).
- Sets initial velocity vector.

## Player
- Player position `G_PlayerX`, `G_PlayerY` is updated by Input.
- Hitbox is hardcoded (approx 4px check in `Stage2` loop).
