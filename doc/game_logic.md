# Game Logic & Mechanics — 特訓９９ (Training 99)

> **Verified against decompiled C code** (`reverse_engineering_ref/decompiled/99.exe.c`)

## 1. Game Overview

A bullet-hell survival game. Objective: avoid bullets. One hit = death. Features 4 difficulty levels, 7 bullet pattern types, a graze scoring system, and a humorous ranking screen.

- **Resolution**: 320×240 (0x140 × 0xF0) — player clamped to 304×224 (0x130 × 0xE0)
- **Frame rate**: ~80 FPS (ScoreType 1), unlocked (ScoreType 2)
- **Window class**: `TKKN`, title: `特訓９９`

## 2. Difficulty vs Score Mode — TWO separate settings

### Difficulty (bullet count) — `G_DifficultyMode` at `0x00406dc0`

| Value | Label | Starting bullets |
|---|---|---|
| 0 | Easy | 30 (0x1E) |
| 1 | Normal (default) | 50 (0x32) |
| 2 | Hard | 100 |
| 3 | Lunatic | 200 |

### Score Mode (multiplier + frame rate) — `G_ScoreType` at `0x00406dc8`

| Value | Multiplier | Frame rate | String |
|---|---|---|---|
| 0 | 16 (0x10) | ~80 FPS | (Standard) |
| 1 | 12 (0xC) | ~80 FPS | "なんとなく80フレーム/秒" |
| 2 | 0 | Unlocked | "勢い余って全速力" |

When multiplier = 0: score = raw survival milliseconds, game runs at max CPU speed.
Multiplier is stored at `G_ScoreMultiplier` (`0x00406d8c`), set during init from ScoreType.

### Natural Difficulty Ramp (during gameplay)

The game has no explicit "level" system — difficulty is fixed. But difficulty increases naturally:

1. **Bullet count ramps**: `G_CurrentBulletCount` starts at the difficulty level
   (30/50/100/200) and increments every 3 seconds on spawn, up to 299 max.
   → More bullets on screen over time.

2. **Patterns activate randomly**: 12.5% chance every 5 seconds to start a pattern
   (Patterns 1-7 introduce harder bullet types: homing, accelerating, chasing).
   Patterns last 100 frames (~1.25s), then cooldown 5s.

3. **Bullet recycling**: Off-screen bullets respawn immediately instead of being
   removed — the bullet count only increases, never decreases.

This means a 60-second run has ~75-100 bullets with ~3-5 pattern activations
(mixing in homing/accel types), while a 10-second run has ~50 bullets with
no patterns active.

## 3. Game State Machine — `G_GameState` at `0x00406d74`

| Value | State |
|---|---|
| 0 | Title screen |
| 1 | Playing (sub-menu navigation mode) |
| 2 | Sub-menu 2 |
| 3 | Sub-menu 3 |
| 4 | Sub-menu 4 |
| 5 | Result / Game Over display |
| 6 | Ranking screen |

Player starts at state 2 (sub-menu), SubState=0, then transitions through sub-menus to state 1 (Playing). Game init sets state to 2.

## 4. Bullet Patterns — `G_NextBulletPattern` at `0x00406dbc`

Patterns cycle randomly: when no pattern is active, 12.5% chance (0x3000/0x10000) of starting one every 5 seconds. Patterns last 100 frames.

| Pattern | Type | Behavior |
|---|---|---|
| 0 | — | No pattern (random Type 0 bullets from edges) |
| 1 | 0 (Normal) | Constant velocity from lookup table |
| 2 | 1 (Homing) | Homing, timer 0x30 (48 update cycles) |
| 3 | 1 (Homing) | Homing, timer 0x20 (32 update cycles) |
| 4 | 1 (Homing) | Homing, timer 0x10 (16 update cycles) |
| 5 | 1 (Homing) | Homing, timer (random%4+1)×16 |
| 6 | 3 (Accel) | Accelerating, uses accel lookup table |
| 7 | 2 (Homing-Accel) | Accelerates toward player, **max 4 on screen** |

## 5. Bullet Types (Detailed)

### Type 0 — Normal
- Constant velocity from `DAT_00405d74` (velocity table, 64 angles × 12 bytes)
- Velocity in RAW units: `raw += v_raw` per frame
- `pixel = (raw >> 6) - 4`

### Type 1 — Homing
- Uses same velocity table as Type 0
- Has a timer (offset 0x0B) and internal counter (offset 3)
- When counter == timer: recalculates angle toward player using `FUN_00402d68`
- Angle adjusts by ±1 per recalculation toward target
- Converts to Type 0 if distance to target angle is too large (≥ 0x28 = 40)

### Type 2 — Homing Acceleration (NOT BOUNCE!)
- **Does NOT bounce off walls** — this is a common misreading of the code
- Accelerates **toward** player position (PlayerX+6, PlayerY+6)
- vx increases by +1 each frame toward player, capped at ±96 (0x60 signed)
- vy increases by +1 each frame toward player, capped at ±96
- Capped at 4 on-screen simultaneously (tracked at `0x00406dac`)
- Velocity stored as signed bytes at offsets 0x0D and 0x0E

### Type 3 — Accelerating
- Uses acceleration table `DAT_00406074` (different table from Type 0/1)
- Same structure: 64 angles × 12 bytes, same coordinate system
- Higher velocity values than the normal table

## 6. Bullet Spawning

- **Spawn locations**: Random on one of 4 screen edges:
  - Top: (random X ∈ [0, 0x5100), Y=0)
  - Bottom: (random X ∈ [0, 0x5100), Y=0x3D00)
  - Left: (X=0, random Y ∈ [0, 0x3D00))
  - Right: (X=0x5100, random Y ∈ [0, 0x3D00))
- **Spawn interval**: Every 3000ms (`G_NextSpawnTime = current_tick + 3000`)
- **Stop condition**: When `G_CurrentBulletCount >= 299` or pattern 7 active (bounce limit)
- `G_CurrentBulletCount` starts at difficulty level (30/50/100/200) and only increases on spawn
- When a bullet goes off-screen (raw_x ≥ 0x5101 or raw_y ≥ 0x3D01), it respawns

## 7. Collision Detection (Hitbox)

From `Stage2_GameEntityLoop.c`:
```c
if ((iVar4 - 2U < 0xb) && (uVar8 < 10))
// where iVar4 = bullet_x_px - player_x_px, uVar8 = bullet_y_px - player_y_px
```

**Exact hitbox**: `2 <= (bx - px) < 13` AND `0 <= (by - py) < 10`

Hitbox is **11px wide × 10px tall**, anchored at player's top-left pixel.

## 8. Graze System

- **Proximity zone**: `(bx-px+4 < 23) AND (by-py+6 < 20)` — roughly a 19×20 px rectangle around player
- When bullet enters zone: `G_ActiveEntityCount++` at `0x00406db4`
- When bullet leaves zone: `G_ActiveEntityCount--`, and `G_TotalEntitiesSpawned += G_ActiveEntityCount` at `0x00406db8`
- This means the graze SCORE increases by the current graze COUNT each time a bullet exits
- Graze chain (`G_PatternCounter` at `0x00406df0`): counts 1–10, resets after 1000ms with no graze
- Graze bar displayed during gameplay via BitBlt

## 9. Player Movement

From `FUN_00403400` (main render/update):
```c
iVar3 = (uint)((G_InputState & 8) != 0) - (uint)((G_InputState & 1) != 0);  // X delta
G_PlayerX = G_PlayerX + iVar3;
G_PlayerY = G_PlayerY + ((uint)((G_InputState & 4) != 0) - (uint)((G_InputState & 2) != 0));
```

- **1 px/frame per axis** — not normalized: diagonals are √2 faster
- Clamped to [0, 0x130] × [0, 0xE0]
- **Start position**: X=0x98 (152), Y=0x2C (44) — upper-left area

### Input Bitmask
```
0  = STOP       3  = UP+LEFT     10 = UP+RIGHT
1  = LEFT       5  = DOWN+LEFT   12 = DOWN+RIGHT
2  = UP
4  = DOWN
8  = RIGHT
```

## 10. Scoring

During gameplay: `G_Score_Time` (at `0x00406d88`) increments by 1 each frame.

At death (in `DrawGameOver`):
- If multiplier ≠ 0: `display_score = G_Score_Time × multiplier`
- If multiplier = 0: display actual survival ms + effective FPS

Ranking: score compared against descending thresholds in ranking table `DAT_004067a3` (8-byte entries).

## 11. RNG

```c
DAT_00405c00 = DAT_00405c00 * 0x343fd + 0x269ec3;
return (DAT_00405c00 >> 0x10) & 0x7FFF;
```
Standard LCG, 15-bit output (0–32767).

## 12. Entity Struct (15 bytes at `0x00406e10`)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0x00–0x03 | 4 | `raw_x` | Raw X (uint32). Pixel = `(raw_x >> 6) - 4` |
| 0x04–0x07 | 4 | `raw_y` | Raw Y (uint32). Pixel = `(raw_y >> 6) - 4` |
| 0x08 | 1 | `angle_index` | Direction index (0xFF = inactive/free slot) |
| 0x09 | 1 | `graze_flag` | 1 = currently grazed by player |
| 0x0A | 1 | `type` | 0=Normal, 1=Homing, 2=Homing-Accel, 3=Accelerating |
| 0x0B | 1 | `timer` | Homing recalculation interval |
| 0x0C | 1 | `index` | Slot/sequence index |
| 0x0D | 1 | `vx` | Direct X velocity (signed byte, used by Type 2) |
| 0x0E | 1 | `vy` | Direct Y velocity (signed byte, used by Type 2) |

Array: 300 slots at `0x00406e10`, each 15 bytes (0x0F). Iteration: `ptr += 0x0F`.

