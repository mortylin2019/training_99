# Stage 3: Ranking Summary

## Overview
Handles the End-Game Ranking screen where the player receives a humorous title based on their performance.

## Logic Breakdown
1. **Ranking Lookup**:
   - Uses `G_Score_Time` (or raw time if Multiplier=0) to search the Ranking Table (`DAT_004067a3`).
   - The table is sorted by descending threshold.
   - Finds the first entry where `Score >= Threshold`.

2. **Text Construction**:
   - A single table entry contains indices for 4 string components: a, b, c, d.
   - **Prefix 1** (Index `[1]`): Small text, top left.
   - **Prefix 2** (Index `[5]`): Small text, top left (appended).
   - **Title** (Index `[6]`): Large central text.
   - **Suffix** (Index `[7]`): Small text, bottom center.

3. **Rendering**:
   - `DrawTextA` with variable font sizes.
   - The central title font size is calculated dynamically: `0x1e0 / length`.
   - Wait for input to return to Start Screen.

## Key Tables
- `0x4067a3`: The Ranking Threshold Table.
- `0x406bf8`: String Pointer Table.
