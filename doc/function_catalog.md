# 99.exe Function Catalog — Complete Behavior Reference

> Auto-generated from `reverse_engineering_ref/decompiled/99.exe.c` (3113 lines)
> Used as ground truth for simulator/test coverage

---

## Function Map

| Address | Name | Lines | Description |
|---------|------|-------|-------------|
| `00402000` | RNG_Step | ~1380 | LCG: `state = state*0x343FD+0x269EC3` |
| `00402d68` | ComputeAimedAngle | 1344–1441 | Bullet→player angle with octant search |
| `00402e88` | SpawnBullet | 1443–1533 | Edge spawn + type/timer/angle init |
| `00402fbc` | EntityLoop | 1535–1730 | Main per-frame bullet processing |
| `00403400` | MainFrame | ~1750 | Player move + entity loop + render |
| `00404660` | GameInit | 2385–2430 | Init entity array, difficulty settings |
| `004046cc` | SessionStart | 2432–2500 | Tab-out pause compensation |

---

## FUN_00402e88 — SpawnBullet

### Position (edges, 4-way uniform)
```
edge = RNG & 3
0 (Top):    raw_x = RNG % 0x5100, raw_y = 0
1 (Bottom): raw_x = RNG % 0x5100, raw_y = 0x3D00
2 (Left):   raw_x = 0,            raw_y = RNG % 0x3D00
3 (Right):  raw_x = 0x5100,       raw_y = RNG % 0x3D00
```

### Field initialization order
| Offset | Field | Init Value |
|--------|-------|-----------|
| 0x0B | timer | 0 |
| 0x0C | counter | 0 |
| 0x09 | grazed | 0 |
| 0x0A | type | 0 (default) |
| 0x0D | vx | NOT cleared (pattern 7 sets to 0) |
| 0x0E | vy | NOT cleared (pattern 7 sets to 0) |
| 0x08 | angle_index | Set by FUN_00402d68 |

### Pattern switch
| Pattern | type | timer | spread | Notes |
|---------|------|-------|--------|-------|
| 0 | 0 | 0 | 5 | Normal, aimed |
| 1 | 0 | 0 | **0** | Normal, PERFECT aim |
| 2 | 1 | 0x30 (48) | 5 | Homing |
| 3 | 1 | 0x20 (32) | 5 | Homing |
| 4 | 1 | 0x10 (16) | 5 | Homing |
| 5 | 1 | ((RNG&3)+1)*16 | 5 | Homing, random timer |
| 6 | 3 | 0 | 5 | Accelerating |
| 7 | 2 | 0 | N/A | H-Accel, no aiming, **returns early** |

### Pattern 7 special handling
```
if bounce_limit < 4:
    bounce_limit += 1
    type = 2
    vx = 0, vy = 0
    RETURN  (no FUN_00402d68 call!)
else:
    type = 0  (fall through to aiming)
```

---

## FUN_00402d68 — ComputeAimedAngle

### Input
- `bullet_raw_x, bullet_raw_y` — raw coordinates
- `player_x, player_y` — pixel coordinates  
- `spread` — jitter amount (0=none, 5=normal, 3=homing re-aim)

### Target computation
```
dx_px = (player_x + 6) - (bullet_raw_x >> 6)   // NO -4 offset!
dy_px = (player_y + 6) - (bullet_raw_y >> 6)
```

### Octant search (C code)
- Divides circle into 8 octants
- Searches ±3 velocity table entries from octant base
- Uses precomputed tan ratios in velocity table (3rd i32 per entry)
- Minimizes angle difference

### Spread jitter
```
if spread != 0:
    angle = (angle + RNG % spread + 1 - spread/2) & 0x3F
```
Spread=5: range = [angle-2, angle+2] (5 values, centered)
Spread=3: range = [angle-1, angle+1] (3 values, centered)
Spread=0: no jitter

---

## FUN_00402fbc — EntityLoop (per-frame)

### Structure
```
do {
    if slot_index >= bullet_count:     // PHASE B (boundary)
        SPAWN CHECK (3 guards)
        PATTERN STATE MACHINE
        return  // exit function
    
    if angle_index == 0xFF:            // inactive slot
        SpawnBullet()
        return  // only ONE inactive fill per frame
    
    if raw_x < 0x5101 AND raw_y < 0x3D01:  // ON-SCREEN
        MOVE BULLET (type-specific)
        RENDER 4×4 block
        if GameOverFlag == 0:
            GRAZE + COLLISION CHECK
    else:                               // OFF-SCREEN
        if type == 2: bounce_limit -= 1
        SpawnBullet()  // immediate respawn
    
    slot_ptr += 15  // next entity
    slot_index += 1
} while(true)
```

### Spawn Check (3 guards)
1. `G_NextSpawnTime < current_time` — timer expired
2. `bullet_count < 299` — NOT 300!
3. `pattern != 7` — Type 2 pattern blocks new spawns

### Pattern State Machine
```
if G_NextPatternTime < current_time:
    if pattern == 0:
        RNG roll
        if roll < 0x3000 (37.5%):
            pattern = (RNG % 7) + 1    // 1-7
            G_PatternDuration = 100
            G_NextPatternTime = now + 10000  // 10s active
        else:
            G_NextPatternTime = now + 5000   // 5s retry
    else:
        pattern = 0
        G_PatternDuration = 100
        G_NextPatternTime = now + 5000       // 5s cooldown
```

### Type-Specific Movement
| Type | Behavior |
|------|----------|
| 0 | `raw += VEL_TABLE[angle*3]` (constant velocity) |
| 1 | Counter++, if >= timer: re-aim(spread=3), counter=RNG&7, steer ±1 or lose-lock→type0 |
| 2 | Pixel comparison to player+6, accelerate ±1 toward target, cap ±96 |
| 3 | `raw += ACCEL_TABLE[angle*12]` (accelerating) |
| else | Falls through to Type 0 movement (same as label LAB_0040326e) |

### Collision (only when GameOverFlag == 0)
```
if dx+4 < 0x17 AND dy+6 < 0x14:           // graze proximity
    if not grazed:
        grazed = 1; active_near++
    if dx-2 < 0xB AND dy < 10:            // ≡ 2≤dx<13, 0≤dy<10
        G_DeathTime = current_time
        G_GameOverFlag = 1
elif was grazed:                            // bullet leaves zone
    grazed = 0; active_near--
    if active_near > 0:
        graze_total += active_near
        if within chain window (<1000ms):
            if chain_counter < 10: chain_counter++
        else:
            chain_counter = 1
        chain_window = now + 1000ms
```

---

## FUN_00404660 — GameInit

```
for i in 0..299:
    entity[i].angle_index = 0xFF  // all inactive

switch difficulty:
    0: bullet_count = 30
    1: bullet_count = 50
    2: bullet_count = 100
    3: bullet_count = 200

bounce_limit = 0
pattern = 0
// NOTE: spawn timer, pattern timer NOT initialized here!
```

---

## FUN_00403400 — MainFrame

```
Read G_InputState bitmask
Move player: dx=(RIGHT-LEFT), dy=(DOWN-UP), clamp to [0,304]×[0,224]
Update G_CurrentTime_Tick = timeGetTime()
Call EntityLoop()
Render via BitBlt
```

### Input Bitmask
| Bit | Direction |
|-----|-----------|
| 1 | LEFT |
| 2 | UP |
| 4 | DOWN |
| 8 | RIGHT |

---

## FUN_004046cc — SessionStart (Tab-Out Compensation)

Called when game window gains/loses focus.
- Adjusts spawn/pattern/graze timers by elapsed pause duration
- Not needed for gameplay simulation

---

## Global Memory Map (complete)

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x00406d6c | G_PlayerX | i32 | Player pixel X (0–304) |
| 0x00406d70 | G_PlayerY | i32 | Player pixel Y (0–224) |
| 0x00406d74 | G_GameState | i32 | 0=Title,1=Playing,5=Result,6=Ranking |
| 0x00406d7c | G_InputState | i32 | Direction bitmask |
| 0x00406d80 | G_GameOverFlag | i32 | 0=alive, 1+=dying |
| 0x00406d84 | G_PauseFlag | i32 | 1=active, 0=paused |
| 0x00406d88 | G_Score_Time | i32 | Score/frame counter |
| 0x00406d90 | G_IsGameRunning | i32 | 1=running |
| 0x00406d94 | G_GameStartTime | i32 | timeGetTime() at start |
| 0x00406d98 | G_DeathTime | i32 | timeGetTime() at death |
| 0x00406d9c | G_TabOutFlag | i32 | 0=focused, else=lost focus |
| 0x00406da0 | PauseAccum | i32 | Pause-adjusted time |
| 0x00406da4 | G_CurrentTime_Tick | i32 | timeGetTime() each frame |
| 0x00406da8 | G_CurrentBulletCount | i32 | Active bullet slots (0–299) |
| 0x00406dac | BounceLimit | i32 | Type 2 counter (max 4) |
| 0x00406db0 | G_PatternDuration | i32 | Pattern display counter (100 at change) |
| 0x00406db4 | G_ActiveEntityCount | i32 | Bullets in graze proximity |
| 0x00406db8 | G_TotalEntitiesSpawned | i32 | Accumulated graze score |
| 0x00406dbc | G_NextBulletPattern | i32 | Active pattern (0–7) |
| 0x00406dc0 | G_DifficultyMode | i32 | 0=Easy,1=Normal,2=Hard,3=Lunatic |
| 0x00406dfc | G_NextSpawnTime | i32 | timeGetTime() + 3000 for next spawn |
| 0x00406e00 | G_NextPatternTime | i32 | timeGetTime() + 5000/10000 for pattern |
| 0x00406e04 | ? | i32 | Set to 100 on graze chain |
| 0x00406e08 | G_GrazeChainTime | i32 | Chain window timer (now+1000) |
| 0x00406e0c | G_PatternCounter | i32 | Graze chain (1–10) |
| 0x00406e10 | G_EntityArray | 300×15 | Bullet entity array |
| 0x00405d74 | VelocityTable | 64×12 | Type 0/1 velocity (vx,vy,tan_ratio) |
| 0x00406074 | AccelTable | 64×12 | Type 3 acceleration |

---

## Test Coverage Matrix

| Behavior | C Source | Test Exists? | Test Name |
|----------|----------|-------------|-----------|
| RNG formula | L1360 | ✅ | test_rng_sequence |
| RNG with seed | L1360 | ✅ | test_rng_seeded |
| Aimed angle: cardinals | L1344 | ✅ | test_aimed_angle_cardinal |
| Aimed angle: spread jitter | L1437 | ✅ | test_aimed_angle_spread |
| Aimed angle: diagonal | L1344 | ✅ | test_aimed_angle_diagonal |
| Spawn: pattern 0 (normal) | L1488 | ✅ | test_spawn_pattern0 |
| Spawn: pattern 1 (perfect) | L1490 | ✅ | test_spawn_pattern1_perfect_aim |
| Spawn: pattern 2 (homing 48f) | L1492 | ✅ | test_spawn_pattern2_homing |
| Spawn: pattern 3 (homing 32f) | L1495 | ✅ | test_spawn_pattern3_homing |
| Spawn: pattern 4 (homing 16f) | L1498 | ✅ | test_spawn_pattern4_homing |
| Spawn: pattern 5 (random) | L1502 | ✅ | test_spawn_pattern5_random_timer |
| Spawn: pattern 6 (accel) | L1510 | ✅ | test_spawn_pattern6_accel |
| Spawn: pattern 7 (H-Accel) | L1513 | ✅ | test_spawn_pattern7_bounce_limit |
| Spawn: edge distribution | L1452 | ✅ | test_spawn_edge_distribution |
| Move: Type 0 | L1668 | ✅ | test_move_type0 |
| Move: Type 1 steer +1 | L1645 | ✅ | test_move_type1_homing_steer |
| Move: Type 1 lose lock | L1652 | ✅ | test_homing_lose_lock |
| Move: Type 1 steer -1 | L1656 | ✅ | test_homing_steer_minus1 |
| Move: Type 2 accel | L1670 | ✅ | test_move_type2_accel |
| Move: Type 2 cap | L1672 | ✅ | (in test_move_type2_accel) |
| Move: Type 3 | L1690 | ✅ | test_move_type3 |
| Collision: hit | L1605 | ✅ | test_collision_hit |
| Collision: all edges | L1605 | ✅ | test_collision_edges |
| Graze: zone entry | L1598 | ✅ | test_graze_zone |
| Pattern: no pattern → start | L1610 | ✅ | test_pattern_no_pattern |
| Pattern: active → end | L1625 | ✅ | test_pattern_end |
| Player: cardinal move | L1750 | ✅ | test_player_move_cardinals |
| Player: diagonal move | L1750 | ✅ | test_player_move_diagonals |
| Player: boundary clamp | L1750 | ✅ | test_player_boundary |
| Pixel: raw→pixel | L1587 | ✅ | test_pixel_conversion |
| Offscreen: detection | L1705 | ✅ | test_offscreen_detection |
| Offscreen: Type 2 bounce-- | L1708 | ✅ | test_process_one_bullet_bounce_decrement |
| Entity: inactive slot fill | L1600 | ✅ | test_process_one_bullet_offscreen |

### Coverage Summary
- **32** total testable behaviors identified
- **32** covered ✅ (100%)
- **0** missing
