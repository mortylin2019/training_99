# Game Logic Specification - "Tokkun" (Special Training)

## Overview
"Tokkun" is a shooting-style game originally developed by "BEE!" in 1999. The objective appears to be dodging or shooting enemies in a confined arena (320x240 resolution).

## Technical Details (Reverse Engineered)

### Architecture
- **Original Platform:** Windows (Win32 API)
- **Resolution:** 320x240 pixels.
- **Frame Rate:** Controlled by `timeGetTime` and `Sleep(1)`. The main loop aims for consistent updates, likely 60FPS given the `Sleep(1)` in a tight loop.

### Game State Machine (`FUN_004042f0`, `FUN_00403ac0`, etc.)
Based on the analysis of the main loop and drawing functions:
- **State 0:** Title Screen / Menu.
- **State 1:** Gameplay.
- **State 2:** Game Over.
- **State 3:** High Score Entry?
- **State 4:** High Score Display.
- **State 5:** Replay?

### Entities (`FUN_00402fbc` Logic)
The game manages a list of entities (up to 300).
Each entity likely creates a structure of ~15-16 bytes.
- **Position (X, Y):** Coordinates on the 320x240 screen.
- **Type/State (`offset 10`):**
    - **Type 1:** Homing behavior? It adjusts its velocity to move towards a target (Player?).
    - **Type 2:** Bouncing behavior. Moves linearly and bounces off screen edges.
    - **Type 3:** Linear movement?
- **Sprite/Appearance:** Rendered using `BitBlt` from a sprite sheet.

### Player Logic
- **Controls:** Arrow Keys (Up, Down, Left, Right).
- **Movement:** Updates player position. Checked against screen boundaries (0,0 to 320,240).
- **Shooting:** Spacebar or Z/X keys (likely mapped to `VK_Z` etc. or simple message loop keys).

### Scoring
- The game tracks time or score (`DAT_00406d88`).
- Scores are displayed at the end.

### Resources
- **Icons:** Standard application icons.
- **Sprites:** The original game constructs graphics at runtime using `CreateDIBSection` (likely procedural or loaded from raw data). However, for the remake, we should use placeholders or extract if possible (but we only have the C code). The code suggests it might be drawing text or simple shapes (`PatBlt`, `BitBlt`).

## Remake Implementation Plan (Flask + JS)
1. **Frontend (JavaScript/Canvas):**
    - Implement the Game Loop (requestAnimationFrame).
    - Implement the Entity System (Player, Enemies, Bullets).
    - Port the movement and collision logic from C to JS.
    - Render to HTML5 Canvas (320x240 scaled up).
2. **Backend (Flask):**
    - Serve the static content.
    - API for Leaderboard (optional but good for "remake" completeness).

