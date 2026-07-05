# Reversed Game Details & Engineering Report - 99.exe

## 1. Core Architecture & Loop
The game runs on a Win32 message loop (`FUN_004042f0`) but relies heavily on `PeekMessageA` to run a continuous game loop when no messages are pending.

- **Main Loop:** `FUN_004042f0`
- **Update/Render Function:** `FUN_00402fbc` (Called repeatedly).
- **Control Rate:** `timeGetTime` is used to regulate the frame rate. The main loop uses `Sleep(0)` to yield when the score multiplier dictates frame pacing, and `WaitMessage()` when game is inactive.

## 2. Difficulty & Score Mode (Two Independent Settings)

**Difficulty** (`G_DifficultyMode` at `0x00406dc0`):
- 0 = Easy (30 bullets)
- 1 = Normal (50 bullets, default)
- 2 = Hard (100 bullets)
- 3 = Lunatic (200 bullets)

**Score Mode** (`G_ScoreType` at `0x00406dc8`):
- 0 = Standard (multiplier 16, ~80 FPS)
- 1 = "なんとなく80フレーム/秒" (multiplier 12, ~80 FPS)
- 2 = "勢い余って全速力" (multiplier 0, unlocked FPS, raw ms scoring)

## 3. Ending & Ranking Logic (`FUN_00404050`)
The game determines the ending screen based on the final score (time survived).

- **Mechanism:** It iterates through a data array at `DAT_004067a3`.
- **Logic:** It compares `Score < Threshold` in a loop.
- **Sorting:** The thresholds are stored in **Descending Order** (Highest requirement first).
- **String Pool Mechanism:** `DAT_004063e4` is not a single string but the start of a **multi-string pool**. The initialization function (`FUN_00402208`) iterates through this memory address, decrypting one null-terminated string at a time, calculating its length, and storing the *pointer* to it in a separate array (`DAT_00406bfc`). This allows the game to access multiple different text lines via index (0, 1, 2...) later.
- **Encryption:** The text for these rankings is stored at `DAT_004063e4` and is **XOR encoded** (Bitwise NOT / `^ 0xFF`) to hide it from simple text searches. It is decoded at runtime by `FUN_004021f4`.

## 4. Entity System & Logic (`Game_EntityLoop`)

The game manages an array of 300 entities at `0x00406e10`. Each entity is 15 bytes (0x0F), iterated as `ptr += 0x0F`.

**Structure (15 bytes):**

| Offset | Size | Field | Description |
|---|---|---|---|
| 0x00–0x03 | 4 | `raw_x` | Raw X (uint32). Pixel = `(raw >> 6) - 4` |
| 0x04–0x07 | 4 | `raw_y` | Raw Y (uint32). Pixel = `(raw >> 6) - 4` |
| 0x08 | 1 | `angle_index` | 0xFF = inactive slot, else angle index (0–63) |
| 0x09 | 1 | `graze_flag` | 1 = currently in graze proximity to player |
| 0x0A | 1 | `type` | 0=Normal, 1=Homing, 2=Homing-Accel, 3=Accelerating |
| 0x0B | 1 | `timer` | Homing recalculation interval (Type 1) |
| 0x0C | 1 | `index` | Internal counter at offset 3, used for homing updates |
| 0x0D | 1 | `vx` | Direct X velocity (signed byte, used by Type 2) |
| 0x0E | 1 | `vy` | Direct Y velocity (signed byte, used by Type 2) |

**Behaviors:**

- **Type 0 (Normal):**
  - Constant linear velocity from lookup table at `DAT_00405d74`
  - 64 angles, 12 bytes per entry: (vx:i32, vy:i32, ?:i32)
  - Movement: `raw_x += vx_raw`, `raw_y += vy_raw` each frame

- **Type 1 (Homing):**
  - Same velocity table as Type 0
  - Internal counter (offset 3) increments each frame
  - When counter == timer (offset 0x0B): recalculates angle toward player using `FUN_00402d68`
  - Angle adjusts by ±1 toward target per cycle
  - Falls back to Type 0 if angular distance is too large (≥ 40 ticks)

- **Type 2 (Homing Acceleration — NOT bounce!):**
  - Accelerates toward player (PlayerX+6, PlayerY+6)
  - vx += 1 toward player each frame, capped at ±96 (0x60)
  - vy += 1 toward player each frame, capped at ±96
  - Capped at 4 on screen (tracked at `0x00406dac`)
  - Velocity stored as signed bytes at offsets 0x0D/0x0E

- **Type 3 (Accelerating):**
  - Uses acceleration table `DAT_00406074` (64 angles × 12 bytes)
  - Similar to Type 0 but with higher velocity values
  - Movement: `raw_x += accel_vx`, `raw_y += accel_vy`

**Rendering (Software Rasterization):**
- Game copies a 4×4 pixel block from `DAT_00405c04` directly into the DIB section at `ppvBits_004069fc`
- No `BitBlt` for bullet sprites — raw pixel copy loop
- DIB: 320×240, 8-bit indexed color, 16-color palette

## 4. Player & Controls
- **Movement:** Standard arrow keys. Logic in `FUN_00403400` handles player updates and rendering.
- **Rendering:** The player is likely rendered similarly (pointers to pixel data).
- **Collision:** The detailed check in `FUN_00402fbc` (likely the complex `if` block checking ranges) confirms AABB (Axis-Aligned Bounding Box) collision.

## 5. Text & UI
- **Method:** `DrawTextA` and `TextOutA` on a GDI Compatible DC (`DAT_004069e4`).
- **Fonts:** Created via `CreateFontIndirectA`. The game uses multiple fonts (Title, Score).
- **Strings:** Stored in a string table (`DAT_00406bf8`) and indexed by score/rank to give the player a "Title" at the end (e.g., "Godlike", "Beginner").

## 6. Resources
