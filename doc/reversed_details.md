# Reversed Game Details & Engineering Report - 99.exe

## 1. Core Architecture & Loop
The game runs on a Win32 message loop (`FUN_004042f0`) but relies heavily on `PeekMessageA` to run a continuous game loop when no messages are pending.

- **Main Loop:** `FUN_004042f0`
- **Update/Render Function:** `FUN_00402fbc` (Called repeatedly).
- **Control Rate:** `timeGetTime` is used to regulate the frame rate implicitly, though the code runs as fast as possible in the `PeekMessage` loop with a `Sleep(1)` in the idle state (or just tight loops).

## 2. Difficulty & Level Progression
The difficulty is determined by a state variable (`DAT_00406dc0`?) which sets the maximum number of simultaneous bullets (`DAT_00406da8`).

**Difficulty Levels:**
- **Max Bullets based on Difficulty:**
  - **Level 0 (Easy):** 30 Bullets.
  - **Level 1 (Normal):** 50 Bullets.
  - **Level 2 (Hard):** 100 Bullets.
  - **Level 3 (Lunatic):** 200 Bullets.

## 3. Ending & Ranking Logic (`FUN_00404050`)
The game determines the ending screen based on the final score (time survived).

- **Mechanism:** It iterates through a data array at `DAT_004067a3`.
- **Logic:** It compares `Score < Threshold` in a loop.
- **Sorting:** The thresholds are stored in **Descending Order** (Highest requirement first).
- **String Pool Mechanism:** `DAT_004063e4` is not a single string but the start of a **multi-string pool**. The initialization function (`FUN_00402208`) iterates through this memory address, decrypting one null-terminated string at a time, calculating its length, and storing the *pointer* to it in a separate array (`DAT_00406bfc`). This allows the game to access multiple different text lines via index (0, 1, 2...) later.
- **Encryption:** The text for these rankings is stored at `DAT_004063e4` and is **XOR encoded** (Bitwise NOT / `^ 0xFF`) to hide it from simple text searches. It is decoded at runtime by `FUN_004021f4`.

## 4. Entity System & Logic (`FUN_00402fbc`)
The game manages an array of ~300 entities. Each entity is a struct (approx 16 bytes).

**Structure:**
- `Offset 0, 1`: X Position (High/Low bytes or Fixed Point).
- `Offset 2, 3`: Y Position.
- `Offset 10`: **Behavior Type**.
- `Offset 11`: State/Timer.

**Behaviors:**
- **Type 1 (Homing - Red/Aggressive):**
  - Calculates angle/vector to player.
  - Adjusts velocity (steering) to follow player.
  - Uses `offset 2` and `offset 3` as velocity accumulators.
- **Type 2 (Bouncing - Yellow/Passive):**
  - Moves linearly.
  - Checks screen boundaries (`0,0` to `320,240`).
  - Inverts velocity component if a wall is hit.
- **Type 3 (Linear?):**
  - Simple `X += VX`, `Y += VY`.

**Rendering (Software Rasterization):**
- The game does **not** use `BitBlt` for sprites.
- It uses a **direct pixel copy loop**.
- It copies a small 4x4 pixel block (from `DAT_00405c04` or similar) directly into the DIB section (`ppvBits_004069fc`).
- This confirms the "retro" look is built by manually blasting bytes into a bitmap buffer.

## 4. Player & Controls
- **Movement:** Standard arrow keys. Logic in `FUN_00403400` handles player updates and rendering.
- **Rendering:** The player is likely rendered similarly (pointers to pixel data).
- **Collision:** The detailed check in `FUN_00402fbc` (likely the complex `if` block checking ranges) confirms AABB (Axis-Aligned Bounding Box) collision.

## 5. Text & UI
- **Method:** `DrawTextA` and `TextOutA` on a GDI Compatible DC (`DAT_004069e4`).
- **Fonts:** Created via `CreateFontIndirectA`. The game uses multiple fonts (Title, Score).
- **Strings:** Stored in a string table (`DAT_00406bf8`) and indexed by score/rank to give the player a "Title" at the end (e.g., "Godlike", "Beginner").

## 6. Resources
- The included `.ico` files are likely for the window frame and taskbar, not in-game assets.
- For the web remake, we should use:
  - **Player:** A simple Green Square (or generated icon).
  - **Bullets:** 4x4 Colored Squares (Red for Homers, Yellow for Bouncers).
  - **Background:** Black.

## 7. Recommendations for Remake
- **Canvas Rendering:** Use `ctx.fillRect` for the 4x4 bullets to match the original's software rasterization vibe.
- **Difficulty Ramp:** Implement a timer that increases `maxEntities` from 30 -> 200 over ~60 seconds.
- **Bullet Patterns:**
  - Start with bouncing bullets (Type 2).
  - Introduce homing bullets (Type 1) after 10-15 seconds.
