# Plan: Modular 99.exe C Reconstruction

## Goal
Replace the old `reverse_engineering_ref/clean_c/` (already deleted) with a new modular, human-readable C reconstruction in `reverse_engineering_ref/src/`. Every function must be verified against radare2 6.1.8 disassembly.

## r2 Verification Summary (already completed by Prometheus)

| Address | Function | Bytes | r2 Verified |
|---|---|---|---|
| 0x402000 | RNG_Step | 29 | `imul eax,[0x405c00],0x343fd; add eax,0x269ec3; sar eax,0x10; and eax,0x7fff` |
| 0x402d68 | ComputeAimedAngle | 288 | Octant dispatch + tan-ratio search ±3 entries in VEL_TABLE |
| 0x402e88 | SpawnBullet | 275 | 4-edge random spawn, 8-pattern dispatch with correct spread values |
| 0x402fbc | EntityLoop | 1092 | Full entity loop: move, collision, graze, spawn, pattern SM |
| 0x403400 | MainFrame | 1671 | Player input→movement→EntityLoop→BitBlt |
| 0x404660 | GameInit | 106 | 300-slot init, difficulty-based count |
| 0x402abc | InputHandler | 620 | Keyboard bitmask set, menu navigation |
| 0x402318 | WindowProc | 661 | Message dispatch to render/input/game |

**Key constants verified:**
- SPAWN_INTERVAL: `add ecx, 0xBB8` = 3000
- PATTERN_RETRY: `add edx, 0x1388` = 5000  
- PATTERN_ACTIVE: `add eax, 0x2710` = 10000
- Type 0 VEL_TABLE access: `mov edx, [eax*4 + 0x405d74]`
- Type 3 ACCEL_TABLE access: `mov edx, [eax*4 + 0x406074]` and `mov eax, [eax*4 + 0x406078]`
- Type 2 acceleration: `inc byte [edx + 0xd]` (vx), cap `cmp al, 0x60`

## Files to Create

```
reverse_engineering_ref/src/
├── types.h          — types, constants, memory map (keep from plan, already well-formed)
├── rng.c            — RNG (0x402000)
├── bullet.c         — ComputeAimedAngle (0x402d68) + SpawnBullet (0x402e88)
├── entity.c         — EntityLoop (0x402fbc), the main per-frame bullet processor
├── game.c           — MainFrame (0x403400) + GameInit (0x404660) + SessionStart (0x4046cc)
├── input.c          — InputHandler (0x402abc) + menu state machine (0x4042f0)
├── render.c         — Background, sprite rendering, BitBlt (0x403400 render section, 0x4025b0, 0x402978, 0x402a30)
├── window.c         — WindowProc (0x402318)
├── main.c           — WinMain entry (0x402020) + window creation (0x402170) + init (0x402208)
└── README.md        — module map with function address index
```

## EXECUTION STEPS

### Step 1: Create `types.h`
Already designed above. Copy the full content from the plan into `reverse_engineering_ref/src/types.h`.

### Step 2: Create `rng.c`
Reconstruct FUN_00402000. The LCG formula verified by r2.

### Step 3: Create `bullet.c`
Reconstruct ComputeAimedAngle (0x402d68) and SpawnBullet (0x402e88) with exact octant logic, tan-ratio search, and pattern dispatch.

### Step 4: Create `entity.c`
Reconstruct the full EntityLoop (0x402fbc) including:
- Slot iteration with inactive slot fill
- Spawn check with 3 guards (timer, count<299, pattern!=7)
- Pattern state machine (37.5% chance, 1-7 patterns)
- Type-specific movement (all 4 types)
- 4×4 pixel bullet rendering
- Graze proximity tracking
- Hitbox collision check
- Off-screen respawn

### Step 5: Create `game.c`
Reconstruct MainFrame (0x403400) with input reading, player movement/clamp, score timer, EntityLoop call, and BitBlt calls. Reconstruct GameInit (0x404660).

### Step 6: Create `input.c`
Reconstruct the keyboard handler (0x402abc) and menu navigation state machine (0x4042f0).

### Step 7: Create `render.c`
Reconstruct the rendering pipeline: background animation, sprite rendering, player sprite, HUD. Covers 0x4025b0 (WM_CREATE), 0x402978 (WM_DESTROY), 0x402a30 (WM_PAINT).

### Step 8: Create `window.c`
Reconstruct WindowProc (0x402318) message dispatch.

### Step 9: Create `main.c`
Reconstruct WinMain entry (0x402020), window creation (0x402170), and initialization (0x402208).

### Step 10: Create `README.md`
Document function-to-address mapping and module structure.

### Step 11: Verify with r2 (basic sanity)
For each source file, grep out addresses and verify against r2 disassembly.

---

## Key correctness requirements (verified against r2)

1. **RNG**: `state = state * 0x343FD + 0x269EC3; return (state >> 16) & 0x7FFF`

2. **ComputeAimedAngle**: Octant determination uses dx/dy sign + magnitude comparisons (8-way dispatch), NOT atan2. Tan ratio = `abs((dx << 10) / dy)`. Search ±3 entries from octant base in VEL_TABLE using precomp_tan field.

3. **SpawnBullet**: Pattern 0 = spread 5 (normal), Pattern 1 = spread 0 (perfect), Pattern 7 early return (no aiming) if bounce_limit < 4.

4. **EntityLoop type switch**: 
   - Type 0 (Normal): add VEL_TABLE[angle].vx/vy to raw_x/raw_y
   - Type 1 (Homing): counter++ per frame, when >= timer: re-aim with spread=3, steer ±1 or lose-lock→type0
   - Type 2 (HomingAccel): pixel compare to player+6, inc/dec vx/vy by 1, cap ±0x60
   - Type 3 (Accel): add ACCEL_TABLE[angle].vx/vy to raw_x/raw_y directly
   - Default: fall through to Type 0 behavior

5. **Collision**: `(u32)(dx-2) < 11 AND (u32)(dy) < 10` — asymmetric hitbox

6. **Pattern SM**: RNG roll < 0x3000 → pattern = (roll % 7) + 1, duration=100, next_time = now+10000. If not: next_time = now+5000

7. **Inactive slot fill**: Only ONE filled per frame, early return after fill.

## START EXECUTION

Run `$start-work` to execute this plan.
