# AGENTS.md — AI Assistant Instructions for `training_99`

## Project Overview

This is a **reverse engineering project** for **特訓９９ (Training 99)**, a Japanese bullet-hell survival game from the early 2000s. The original binary (`raw/99.exe`) has been decompiled via Ghidra and analyzed. Python "AI hijack" bots attach to the live game process via `ReadProcessMemory`/`WriteProcessMemory`, read bullet positions and game state, and play the game autonomously via direct input bitmask writes.

**Goal:** Understand the original game mechanics and build AI players that survive the bullet-hell patterns.

---

## Repository Structure

| Directory | Purpose |
|---|---|
| `reverse_engineering_ref/` | Decompiled C code (Ghidra output), memory maps, string tables |
| `reverse_engineering_ref/decompiled/` | Raw `99.exe.c`, hex dumps, manual string overrides |
| `reverse_engineering_ref/python_breakdown/` | Refactored C modules split by game stage |
| `reverse_engineering_ref/resources/` | Extracted icons, version info |
| `doc/` | Human-readable analysis: game logic, entities, state machine, ranking |
| `hijack_tools/` | Python bots that attach to the **live game process** and play |
| `tools/` | Reverse engineering helper scripts |
| `raw/` | Original game binary |
| `logs/` | AI bot runtime logs |

---

## Key Technical Details

### Complete Memory Map (from decompiled code)

#### Player State
| Address | Name | R/W | Description |
|---|---|---|---|
| `0x00406d6c` | `G_PlayerX` | R/W | Player X (pixels, 0–0x130) |
| `0x00406d70` | `G_PlayerY` | R/W | Player Y (pixels, 0–0xE0) |
| `0x00406d7c` | `G_InputState` | R/W | **Bitmask hijack point** — write direction here |

#### Game State Machine
| Address | Name | Description |
|---|---|---|
| `0x00406d74` | `G_GameState` | 0=Title, 1=Playing, 2-4=SubMenus, 5=Result, 6=Ranking |
| `0x00406d78` | `G_SubState` | Sub-menu cursor position |
| `0x00406d80` | `G_GameOverFlag` | 0=alive, 1=dead (increments to 0x11 during death anim) |
| `0x00406d84` | `G_PauseFlag` | 1=Active/Playing, 0=Paused/Menu |
| `0x00406d90` | `G_IsGameRunning` | 1=running |

#### Timing
| Address | Name | Description |
|---|---|---|
| `0x00406d88` | `G_Score_Time` | Frame counter (incremented each frame alive) |
| `0x00406d8c` | `G_ScoreMultiplier` | 16 (Standard), 12 (Mode 2), 0 (Mode 3) |
| `0x00406d94` | `G_GameStartTime` | `timeGetTime()` at session start |
| `0x00406d98` | `G_DeathTime` | `timeGetTime()` when player died |
| `0x00406da4` | `G_CurrentTime_Tick` | Current `timeGetTime()` |
| `0x00406da0` | Pause accum | Pause-adjusted time accumulator |
| `0x00406d9c` | Tab-out flag | 0=focused, else=window lost focus |

#### Entity / Bullet System
| Address | Name | Description |
|---|---|---|
| `0x00406da8` | `G_CurrentBulletCount` | Active bullet count |
| `0x00406dac` | Bounce limit | Bounce bullet counter (max 4, then stops spawning Type 2) |
| `0x00406db4` | `G_ActiveEntityCount` | Bullets in graze proximity to player |
| `0x00406db8` | `G_TotalEntitiesSpawned` | Accumulated graze score |
| `0x00406e10` | `G_EntityArray` | 300 × 15 byte bullet entities |

#### Bullet Pattern / Spawning
| Address | Name | Description |
|---|---|---|
| `0x00406dbc` | `G_NextBulletPattern` | Current pattern: 0=none, 1-7=active |
| `0x00406db0` | `G_PatternDuration` | Remaining frames for current pattern |
| `0x00406dfc` | `G_NextSpawnTime` | Timestamp for next bullet spawn |
| `0x00406e00` | `G_NextPatternTime` | Timestamp for pattern change |
| `0x00406df0` | `G_PatternCounter` | Graze chain counter (1-10) |

#### Difficulty / Mode
| Address | Name | Description |
|---|---|---|
| `0x00406dc0` | `G_DifficultyMode` | 0=Easy(30), 1=Normal(50), 2=Hard(100), 3=Lunatic(200) |
| `0x00406dc4` | BG mode | 0=off, 1=grayscale, 2=noise |
| `0x00406dc8` | `G_ScoreType` | 0, 1, 2 |
| `0x00406dcc` | `G_HighPriorityMode` | Process priority flag |

#### Lookup Tables (read once at init)
| Address | Name | Description |
|---|---|---|
| `0x00405d74` | Velocity table | Type 0/1: 64 angles × 12 bytes (vx:i32, vy:i32, ?:i32) |
| `0x00406074` | Accel table | Type 3: 64 angles × 12 bytes |

#### Bullet Pattern Reference (from `Bullet_Mechanics.c`)
| Pattern | Type | Behavior |
|---|---|---|
| 1 | Type 0 | Normal, constant velocity |
| 2 | Type 1 | Homing, timer=0x30 (48 frames) |
| 3 | Type 1 | Homing, timer=0x20 (32 frames) |
| 4 | Type 1 | Homing, timer=0x10 (16 frames) |
| 5 | Type 1 | Homing, timer=random×16 |
| 6 | Type 3 | Accelerating |
| 7 | Type 2 | Bounce, max 4 on screen |

### Bullet Entity Structure (15 bytes at `0x00406e10`)
- `+0x00-0x07`: `raw_x`, `raw_y` (raw internal coords; pixel = `(raw >> 6) - 4`)
- `+0x08`: `angle_index` (0xFF = inactive)
- `+0x09`: `active` flag
- `+0x0A`: `type` (0=Normal, 1=Homing, 2=Bounce, 3=Accelerating)
- `+0x0B`: `timer`
- `+0x0C`: `index`
- `+0x0D-0x0E`: `vx`, `vy` (direct speed for Type 2)

### Input Bitmask
```
1  = LEFT      3  = UP+LEFT     5  = DOWN+LEFT
2  = UP        10 = UP+RIGHT    12 = DOWN+RIGHT
4  = DOWN      0  = STOP
8  = RIGHT
```

### Collision Detection
From `Stage2_GameEntityLoop.c`: Hit if `2 <= (bullet_x - player_x) < 13 AND 0 <= (bullet_y - player_y) < 10`.

### Frame Rate
Target ~80 FPS. Movement is **1 px/frame** in each direction (diagonals = 1px both axes, NOT normalized).

---

## Hijack Tools Architecture

All AI bots follow this pattern:
1. Launch `99.exe` via `subprocess.Popen`
2. Attach via `OpenProcess` / `ReadProcessMemory` / `WriteProcessMemory`
3. Read player position, bullets, game state each frame
4. Decide a movement direction
5. Write the bitmask to `0x00406d7c`

### AI Versions (increasing sophistication)
| File | Approach | Notes |
|---|---|---|
| `ai_basic.py` | Safety Map / Danger Field | Inverse-square danger scoring, 9-move evaluation, center bias |
| `ai_1.py` | Vector Repulsion | Sum of normalized repulsion vectors, home pull to center |
| `ai_2.py` | Grid Danger Scoring | 5px grid, prediction of bullet positions, center-pull gravity |
| `ai_3.py` | Oracle / Two-Stage Lookahead | 60-frame simulation, 81-path branching, exact hitbox check |
| `ai_4.py` | Time-Space A\* | 2x2px grid, 160-frame lookahead, vectorized numpy prediction |
| **`ai_direct.py`** | **Time-Space Danger Grid + Full State** | **Uses ALL decompiled data: velocity tables from memory, pattern info, spawn timing, graze counters, multi-frame lookahead with exact hitbox. Bitmask hijack control.** |

### Control Mechanism (IMPORTANT)

There are three ways to control the player, from worst to best:

1. **Keyboard SendMessage** (`send_key`/`move_up` etc.) — Sends `WM_KEYDOWN`/`WM_KEYUP` to the game window. SLOW, unreliable, only used for menu navigation (pressing Enter).

2. **Input Bitmask Hijack** (`write_int(0x00406d7c, bits)`) — **THE CORRECT APPROACH.** Writes the direction bitmask directly to `G_InputState`. The game reads this each frame and moves the player 1px/frame. This is true process hijack — no Windows messages, no keyboard involved.

3. **Direct Position Write** (`write_int(0x00406d6c, x)`) — Teleports the player instantly. Works but is cheating/unrealistic. DO NOT USE for gameplay AI.

### Key Dependencies
- `pywin32` / `ctypes` for Windows process memory access
- `numpy` for vectorized bullet prediction (ai_4, ai_direct)
- `loguru` for structured logging

---

## Reverse Engineering Tools

- `breakdown_and_translate.py`: Splits monolithic decompiled C into logical modules, decodes Shift-JIS strings, renames variables
- `reverse_data.py`: Extracts encrypted ranking table, exports as JSON
- `analyze_exe_strings.py`, `dump_all_strings.py`, `dump_table.py`: String/data extraction utilities

---

## Coding Conventions

1. **Python**: Use `loguru` for logging (not `print` or `logging`). Use type hints where helpful.
2. **Memory access**: Always go through `GameControl.read_int()`/`write_int()` — never use raw ctypes in AI scripts.
3. **Import pattern**: Hijack tools use a `try/except ImportError` pattern to work both as standalone scripts and as imported modules:
   ```python
   try:
       from game_control import GameControl
   except ImportError:
       from hijack_tools.game_control import GameControl
   ```
4. **Input writing**: Always call `self.game.write_int(0x00406d7c, 0)` (STOP) when exiting or changing state to prevent stuck keys.
5. **Bullet filtering**: Always filter inactive bullets: `[b for b in bullets if b.angle_index != 0xFF]`.
6. **Control mechanism**: Use **input bitmask hijack** (`write_int(0x00406d7c, bits)`) for gameplay AI. NEVER use keyboard `SendMessage` for movement (slow/unreliable). NEVER use direct position write (`write_int(0x00406d6c, x)`) — that's teleport cheating.

---

## Important Notes for AI Assistants

- The original game binary is **32-bit Windows**, compiled with what appears to be an older C compiler (possibly Visual C++ 6 or similar).
- The decompiled C code in `reverse_engineering_ref/python_breakdown/` has been manually cleaned up and annotated — it's the canonical reference for game logic.
- `doc/game_logic.md` is the authoritative documentation of game mechanics.
- The hijack tools require the **actual game binary** (`raw/99.exe`) running on Windows. They will not work without it.
- Ranking data is XOR-encrypted with `0xFF` in the hex dump.
- Strings are Shift-JIS encoded.
- The window class is `TKKN`, and the window title is `特訓９９`.
- Player hitbox is asymmetric: 11px wide (2-12 offset) × 10px tall (0-9 offset).
- Diagonal movement is **not normalized** — moving diagonally is faster than cardinal movement.
