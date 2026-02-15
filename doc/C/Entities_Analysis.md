# Entity Management and Logic

## Overview
Based on the analysis of `Stage2_GameEntityLoop.c` and `Bullet_Mechanics.c`, the game uses a fixed array of entity structures.

## Entity Array Logic
- **Fixed Size**: The game iterates through an array of entities using an index (0 to 299).
- **Active Limit**: `G_CurrentBulletCount` controls how many entities in the array are currently "active" (rendering and updating).
- **Respawn on Death**: 
  - Unlike modern engines that destroy and create objects, this game **recycles** slots immediately.
  - When an entity goes out of bounds (coordinates `>= 0x5101` or `>= 0x3d01`), the game logic falls into the `else` block.
  - It calls `Entity_SpawnBullet()`, which re-initializes the *current* slot with new random coordinates and type.
  - **There is no "remove" logic**. The count `G_CurrentBulletCount` only *increases* (via the spawn timer logic at the top of the loop). It never decreases during gameplay.

## Type 2 (Bouncing/Pattern 7) Exception
- There is a special counter `DAT_00406dac` (likely "Active Bouncers").
- If a bullet with specific flags/type (checked via `(*(byte *)((int)local_2c + 10) & 2) != 0`) goes out of bounds:
  - It decrements `DAT_00406dac--`.
  - It *still* calls `Entity_SpawnBullet()` to recycle the slot, potentially becoming a different type.

## Implications for Remake
- The remake's `entities` array logic (delete and re-spawn) mimics the C logic functionally with simpler JS idioms.
- **Critical Fix**: The previous remake had a bug where newly spawned Type 2 entities (Bouncing) would immediately bounce off the screen edge and fly away, creating an empty screen but high entity count. This was fixed by checking velocity direction before bouncing.

## Spawning Logic
- `Entity_SpawnBullet` sets coordinates to 0 or Max (screen edges).
- Types are randomly assigned:
  - 0: Pattern 0
  - 1: Pattern 1 (Homing?)
  - 2: Pattern 2 (Bounce?)
  - 3: Pattern 3 (Accel?)
