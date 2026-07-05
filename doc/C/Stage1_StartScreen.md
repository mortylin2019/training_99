# Stage 1: Start Screen

## Overview
The initial menu screen where the user selects difficulty.

## Logic Breakdown
1. **Difficulty Display**:
   - Checks `G_DifficultyMode` (0, 2, 3) and `G_HighPriorityMode`.
   - Displays relevant strings:
     - Standard: (Implicit default)
     - Mode 2: "調子に乗って 100発"
     - Mode 3: "怒濤の 200発"
   - Shows system status strings (e.g., "Yield Process", "80fps").

2. **Input Handling**:
   - Calls `Sys_InputTimerUpdate`.
   - Use Enter/Space to start `MainLoop`.

## Key Strings
- `0x405c51`: Window Name / Title.
- `0x405d15`: "Enterで特訓開始" (Start Training with Enter).
