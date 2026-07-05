# Stage 4: Game Over Display

## Overview
Handles the display of the Game Over screen, showing statistics such as survival time, score, and the "Exquisite Degree" (Graze/Risk metric).

## Logic Breakdown
1. **Background Setup**:
   - Sets background color to Black.
   - Sets Text color to White (0xFFFFFF).

2. **Title Display**:
   - Displays "失格" (Disqualified/Failure) at the top of the screen.
   - Uses a large font.

3. **Statistics Display**:
   - **Survival Time**: Calculated from `G_DeathTime - G_GameStartTime`.
   - **Activity Time**: Calculated from `G_Score_Time * Multiplier` (if Multiplier != 0).
   - **Bullet Count**: Displays `G_CurrentBulletCount`.
   - **Exquisite Degree (絶妙度)**: Displays `G_TotalEntitiesSpawned` as a percentage.
     - *Note*: Despite the name `G_TotalEntitiesSpawned` in legacy breakdown, analysis suggests this variable tracks "Graze Points" or accumulated risk. It increments when bullets leave the player's proximity zone while other bullets remain close.

4. **Input Handling**:
   - Updates `G_PauseFlag` to 5 (Waiting for input on Game Over).
   - Upon input, transitions to Stage 3 (Ranking).

## Key Functions
- `DrawGameOver(startTime, duration)`: Main rendering routine.
