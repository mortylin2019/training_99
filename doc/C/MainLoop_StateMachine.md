# Main Loop: State Machine

## Overview
The primary application loop (`MainLoop_StateMachine` + `entry` in `Util_Random.c`).

## Logic Breakdown

1. **Prioritization**:
   - `G_HighPriorityMode`: Sets process to `HIGH_PRIORITY_CLASS` (0x80) and thread to `THREAD_PRIORITY_HIGHEST` (2)
   - Background mode: allocates 0x12C00 bytes of heap for scrolling background when BG mode ≠ 0

2. **Game State**:
   - `G_GameState` at `0x00406d74`: 0=Title, 1=Playing(submenu), 2-4=SubMenus, 5=Result, 6=Ranking
   - Init sets state to 2, SubState to 0
   - `G_PauseFlag` at `0x00406d84`: 0=Menu, 1=Playing, 5=ResultDisplay, 6=RankingDisplay
   - `G_IsGameRunning` at `0x00406d90`: 1 when game is actively running

3. **Main Loop** (in `entry`):
   - `PeekMessageA` with PM_REMOVE
   - When no messages: update `G_CurrentTime_Tick = timeGetTime()`
   - If game not running or tabbed out: `WaitMessage()`
   - If multiplier=0 (unlocked FPS) or timestamp condition met: `Sleep(0)`, then render via `FUN_00403400`, advance `DAT_00406da0 += multiplier`

4. **Score Multiplier**:
   - Set from `G_ScoreType` (0x00406dc8):
     - 0 → 0x10 (16, standard)
     - 1 → 0xC (12, "80fps")
     - 2 → 0 (unlocked, raw ms)

5. **Cleanup** (`FUN_00404590`):
   - Called when `G_GameOverFlag` reaches 0x11 (death animation complete)
   - Restores cursor, lowers priority, frees heap
   - Flushes pending WM_KEYDOWN/WM_KEYUP messages
   - Routes to DrawStartScreen (alive) or DrawGameOver (dead)

## Key Functions
- `MainLoop_StateMachine` → init + state setup
- `entry` (in Util_Random.c) → main PeekMessage loop
- `FUN_00403400` → background + entity loop + player + render (called every frame)
- `FUN_00404590` → cleanup / death transition
