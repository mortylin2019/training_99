# Game Logic & Mechanics Documentation

## 1. Game Overview
**99.exe** is a "bullet hell" survival game where the objective is to avoid colliding with bullets for as long as possible. The game features multiple difficulty settings and a ranking system based on survival time and scoring constants.

## 2. Core Loop
- **Initialization**: Sets up the heap, initializes the random number generator, and configures the `G_ScoreMultiplier` based on the difficulty.
- **Game Speed**: The game runs with a target frame rate of roughly **80 FPS** (referenced in string `なんとなく80フレーム/秒`).
- **End Condition**: The game ends immediately upon collision with a bullet.

## 3. Difficulty Modes
The difficulty is selected at the start screen:
1.  **Standard Mode** (Default)
    - Multiplier: `0x10` (16)
    - Entity Count: Standard progression.
2.  **Mode 2** (`調子に乗って 100発`)
    - Multiplier: `0xC` (12)
    - Starts with higher bullet density or cap (100?).
3.  **Mode 3** (`怒濤の 200発`)
    - Multiplier: `0` (This seems like a raw survival mode or "Full Speed" mode).
    - Starts with massive bullet density (200?).

## 4. Scoring System
The score is calculated differently depending on the mode (`G_ScoreMultiplier`):
- **Raw Survival Mode** (Multiplier 0):
  - `Score = Survival Time (ms)`
  - Used in high-density modes where survival itself is the feat.
- **Scoring Mode** (Multiplier > 0, e.g., 16 or 12):
  - `Score = FramesAlive * Multiplier`
  - Since the game runs at ~80 FPS:
    - `1 Second` ≈ 80 Frames.
    - `Score/Sec` ≈ 80 * 16 = 1280 points/sec (Standard)
    - Compare to 1000 points/sec for raw milliseconds. This treats standard mode play as "worth" 1.28x raw time.

## 5. Ranking & Ending System
- Upon death, the "Game Over" screen displays statistics (Score, Time, Bullets, etc.).
- Pressing input advances to the **Ranking Screen** (`Stage3_DeadRankingSummary.c`).
- The ranking depends on the score/time compared against the **Ranking Table** (`DAT_004067a3`).
- **Structure of Ranking Text**:
  - The table entry provides 4 string IDs.
  - **Top-Left**: `Prefix1` + `Prefix2` (e.g., "サル以下の貴様を" "便所掃除") -> Note: Example suggests logic, code confirms concatenation.
  - **Center (Large Font)**: `RankTitle` (e.g., "便所掃除"). Font size scales to fit width.
  - **Bottom**: `Suffix` (e.g., "に任命する。活躍を期待する。").
- **Verification**: The string "Toilet Cleaning" (`便所掃除`) appears as a Title in the middle of the screen.

## 6. Entity Mechanics
- **Player**:
  - Controlled via Arrow Keys.
  - Small hitbox (approx 4x4 pixels center).
- **Bullets**:
  - **Type 1 (Homing/Simple)**: Uses a lookup table for movement patterns.
  - **Type 2 (Bounce/Reflect)**: Bounces off screen edges.
  - **Type 3 (Accelerating)**: Uses a different movement table.
- **Spawning**:
  - Occurs periodically based on `G_NextSpawnTime`.
  - Max bullets: 299.
  - `G_ActiveEntityCount` tracks bullets near the player (possible grazing mechanic, though not directly adding to score in the breakdown).

## 7. Controls
- **Arrow Keys**: Move
- **Space/Enter**: Start Game / Retry
- **Esc**: Quit / Pause (in some contexts)

## 8. Technical Details
- **Memory**: The game allocates a large heap buffer for entity management.
- **Strings**: Text is encoded in Shift-JIS and XOR-obscured in the binary.
- **Window Handling**: Input is processed via `PeekMessage` loops, with prioritized thread execution in some configurations.

