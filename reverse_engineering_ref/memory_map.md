# Memory Map and Symbols

This document maps decompiled variable names and functions to human-readable descriptions based on reverse engineering analysis.

> Source: `reverse_engineering_ref/decompiled/99.exe.c` (3113 lines, 78KB)

## Functions

| Original Name | Human Readable Name | Description |
| :--- | :--- | :--- |
| `FUN_004042f0` | `MainLoop_StateMachine` | Main entry point for the game logic loop. Handles state transitions. |
| `FUN_00403ac0` | `DrawStartScreen` | Renders the title/start screen. |
| `FUN_00402fbc` | `Game_EntityLoop` | Main gameplay update loop. Iterates through entities (bullets, etc.). |
| `FUN_004046cc` | `Sys_InputTimerUpdate` | Handles input processing and updates the global timer (`timeGetTime`). |
| `FUN_00404050` | `Game_CalculateRanking` | Determines the player's rank/title upon death based on survival time and difficulty. |
| `FUN_00403d84` | `DrawGameOver` | Renders the Game Over screen with the calculated title. |
| `FUN_00402e88` | `Entity_SpawnBullet` | Handling Spawning of new bullets. |
| `FUN_00402000` | `Util_Random` | Random number generator wrapper. |
| `FUN_00404660` | `Game_Init` | Initializes game state variables before a run. |
| `FUN_004025b0` | `Entity_UpdateMovement` | (Inferred) Updates position of entities based on their type/velocity. |
| `FUN_00402a30` | `Entity_Type1_Homing` | Behavior logic for "Type 1" entities (likely homing missiles). |
| `FUN_00402978` | `Entity_Type2_Bounce` | Behavior logic for "Type 2" entities (likely bouncing balls). |

## Global Variables

| Original Name | Human Readable Name | Description |
| :--- | :--- | :--- |
| `DAT_00406d88` | `G_Score_Time` | **Survival Time / Score**. Incremented every frame/tick during gameplay. |
| `DAT_00406da4` | `G_CurrentTime_Tick` | Current logical game time tick or frame counter. |
| `DAT_00406d94` | `G_GameStartTime` | Timestamp (`timeGetTime`) when the current game session started. |
| `DAT_00406da8` | `G_CurrentBulletCount` | Initial bullet count at game start (30/50/100/200 based on difficulty). Increments when new bullets spawn. Compared against entity loop index to trigger spawns. |
| `DAT_00406dc0` | `G_DifficultyMode` | Game difficulty: 0=Easy(30 bullets), 1=Normal(50), 2=Hard(100), 3=Lunatic(200). |
| `DAT_00406dc8` | `G_ScoreType` | Likely controls which score multiplier is used (0, 1, 2). |
| `DAT_00406d8c` | `G_ScoreMultiplier` | Multiplier applied to the score (e.g., 0x10, 0xC, 0). |
| `DAT_00406e10` | `G_EntityArray` | The main array storing entity structures (position, type, state). |
| `DAT_00406a00` | `G_HeapMemory` | Pointer to allocated heap memory (0x12C00 bytes). |
| `DAT_004069e4` | `G_BackBufferDC` | Handle to the Device Context (DC) for the back buffer (double buffering). |
| `DAT_004069e0` | `G_SpriteDC` | Handle to the DC containing sprite/resource bitmaps. |
| `DAT_00406d80` | `G_GameOverFlag` | Boolean flag: 1 if player is dead/game over, 0 otherwise. |
| `DAT_00406d74` | `G_GameState` | Current Game State ID (0=Title, 1=Play, 2=Dead...). |
| `DAT_00406d84` | `G_PauseFlag` | Flag indicating if the game is paused or window is inactive. |
| `DAT_00406dcc` | `G_HighPriorityMode` | Flag for process priority class. |
| `DAT_00406dbc` | `G_NextBulletPattern` | Cyclic counter (0-7) determining the next bullet spawn pattern. |
| `DAT_00406dfc` | `G_NextSpawnTime` | Timestamp for the next bullet spawn event. |
| `DAT_00406e00` | `G_NextPatternTime` | Timestamp for changing the bullet pattern. |
| `DAT_00406d98` | `G_DeathTime` | Timestamp when the player died. |
| `DAT_00406d6c` | `G_PlayerX` | Player X Coordinate (Screen Center ~152 / 0x98). |
| `DAT_00406d70` | `G_PlayerY` | Player Y Coordinate (Screen Center ~44 / 0x2C). |
| `_DAT_00406db0` | `G_PatternTimer` | Timer/Counter for the current pattern duration. |

## Structs (Inferred)

**Entity Struct (15 bytes at `0x00406e10`)**

```c
struct Entity {
    uint32_t raw_x;       // offset 0x00 — raw X (pixel = (raw >> 6) - 4)
    uint32_t raw_y;       // offset 0x04 — raw Y
    uint8_t  angle_index; // offset 0x08 — 0xFF = inactive slot
    uint8_t  graze_flag;  // offset 0x09 — 1 = being grazed
    uint8_t  type;        // offset 0x0A — 0=Normal, 1=Homing, 2=HomingAccel, 3=Accel
    uint8_t  timer;       // offset 0x0B — homing recalculation interval
    uint8_t  index;       // offset 0x0C — internal counter
    int8_t   vx;          // offset 0x0D — signed X velocity (Type 2)
    int8_t   vy;          // offset 0x0E — signed Y velocity (Type 2)
};
// sizeof = 15 (0x0F), iterated as ptr += 0x0F
```
