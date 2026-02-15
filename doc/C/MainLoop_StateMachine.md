# Main Loop: State Machine

## Overview
The primary application loop (`MainLoop_StateMachine`).

## Logic Breakdown
1. **Prioritization**:
   - `G_HighPriorityMode`: Sets Windows Process priority to `REALTIME` (dangerous!) to ensure game consistency.
   - `G_HeapMemory`: Allocates game heap (1 MB or more).
   - Initializes RNG seeds (`Util_Random`).

2. **Game State**:
   - `G_GameState`: 0 (Init), 1 (Playing), 2 (Game Over), 3 (Ranking).
   - `G_GameStartTime`: TimeGetTime() snapshot.

3. **Loop**:
   - While message loop is active:
     - Check `PeekMessage`.
     - Update timer (`Sys_InputTimerUpdate`).
     - Render frame (`Stage2_GameEntityLoop`).

4. **Scoring Logic**:
   - Sets `G_ScoreMultiplier`.
   - `0x10` (Standard)
   - `0xC` (Mode 2)
   - `0` (Mode 3 - Raw Time)

## Key Functions
- `MainLoop_StateMachine`
- `FUN_00404590` (Likely the input/timer update hook).
