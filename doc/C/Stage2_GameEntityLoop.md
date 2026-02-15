# Stage 2: Entity Loop / Game Logic

## Overview
This file contains the core game logic for the PLAYING state (`Game_EntityLoop`).

## Logic Breakdown
1. **Bullet Updates**:
   - Iterates through the global entity array.
   - For each active bullet:
     - Updates position based on Type (1, 2, 3).
       - **Type 1**: Homing behavior (`Util_Random` and lookup tables).
       - **Type 2**: Bounce behavior (`G_Collision` check).
       - **Type 3**: Acceleration behavior.
     - Performs collision detection with player.

2. **Collision Detection**:
   - Checks proximity between Bullet and Player (`G_PlayerX`, `G_PlayerY`).
   - If distance < Hitbox Threshold:
     - Sets `G_GameOverFlag = 1`.
     - Sets `G_DeathTime = G_CurrentTime_Tick`.

3. **"Exquisite Degree" (Risk) Calculation**:
   - The variable `G_TotalEntitiesSpawned` (likely misnamed in initial breakdown, actually `G_GrazeScore`) accumulates when bullets are in close proximity to the player.
   - Logic: When a bullet *leaves* the proximity zone, if other bullets remain close (`G_ActiveEntityCount != 0`), the counter increments. This rewards staying near multiple bullets.
   
4. **Spawning Logic**:
   - Checks `G_NextSpawnTime`.
   - Checks `G_CurrentBulletCount < 299`.
   - Calls `Entity_SpawnBullet` to create new threats.

## Key Variables
- `G_EntityArray`: Main storage for bullets.
- `G_ActiveEntityCount`: Seems to track bullets *currently* within a danger/graze radius, not total global count.
