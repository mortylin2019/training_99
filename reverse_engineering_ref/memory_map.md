# Memory Map and Symbols

This document maps decompiled variable names and functions to human-readable descriptions based on reverse engineering analysis.

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
| `DAT_00406da8` | `G_CurrentBulletCount` | Current number of active bullets (capped at 300). Increases over time. |
| `DAT_00406dc0` | `G_DifficultyMode` | Game difficulty setting (0=Normal, 2=Hard/100 Bullets?). |
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

**Entity Struct (approx 16 bytes)**
```c
struct Entity {
    short x;          // offset 0
    short y;          // offset 2
    short vx;         // offset 4
    short vy;         // offset 6
    byte type;        // offset 8?
    byte state;       // offset 9
    // ... padding or other fields
};
```
