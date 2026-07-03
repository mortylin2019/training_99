# Plan: ESIL-vs-Simulator Exhaustive Cross-Validation

## Goal
Prove the Python simulator matches 99.exe instruction-by-instruction using r2 ESIL.
No C code needed — the Python simulator IS the ground-truth representation.

## Strategy

For each gameplay function, set identical initial state in both ESIL and Python,
run both, then diff registers and memory writes. Every mismatch means a simulator bug.

## Test Matrix

### 1. RNG (0x402000) — 10 seeds × 100 iterations
- 10 different seeds covering edge values (0, 0xFFFFFFFF, 0x80000000, etc.)
- Chain 100 iterations each
- Compare all 100 outputs (ESIL vs Python LCG)
- 1,000 validation points total

### 2. ComputeAimedAngle (0x402d68) — 8 octants × 3 spreads × 3 distances
- 8 cardinal/ordinal directions (one per octant)
- Spread values: 0 (perfect), 3 (homing), 5 (normal)
- 3 distances: near (10px), mid (100px), far (edge of screen)
- Also test degenerate cases: dx=0, dy=0, bullet at player position
- Verify angle_index output matches
- ~80 test cases

### 3. SpawnBullet (0x402e88) — 8 patterns × 4 edges
- All 8 patterns (0-7)
- All 4 spawn edges (top/bottom/left/right)
- Verify type, timer, angle_index, vx/vy fields match
- ~40 test cases

### 4. Bullet Movement — 4 types × 10 frames
- Type 0 (Normal): verify VEL_TABLE lookup + raw_x/raw_y delta
- Type 1 (Homing): verify counter++, re-aim trigger, steer logic, lose-lock
- Type 2 (HomingAccel): verify acceleration toward player, cap at ±96
- Type 3 (Accel): verify ACCEL_TABLE lookup
- Run 10 frames each, compare position after each frame
- ~40 trajectory tests

### 5. Collision Detection — hitbox edges
- Bullet exactly at hitbox boundary (hits and misses)
- All 4 edges of the 11×10 hitbox
- Verify G_GameOverFlag gets set correctly
- ~20 test cases

### 6. Graze Logic — entry/exit
- Bullet entering graze zone → verify G_ActiveEntityCount++
- Bullet leaving graze zone → verify graze scoring and chain counter
- ~15 test cases

### 7. Pattern State Machine — transitions
- Force pattern 0 → random roll → pattern 1-7 activation
- Force active pattern → pattern 0 deactivation
- Verify G_PatternDuration, G_NextPatternTime
- ~10 test cases

## Files to Create

### `tools/verify_esil_full.py`

Main harness. Structure:

```python
class ESILHarness:
    """Controls r2 ESIL VM via r2pipe."""
    
    def __init__(self, exe_path):
        self.r2 = r2pipe.open(exe_path, ["-e","bin.relocs.apply=true"])
        self.r2.cmd("aaaa")
    
    def set_memory(self, addr, value, size=4):
        """Write value to ESIL memory."""
        self.r2.cmd(f"wv{size} {value} @ {addr}")
        self.r2.cmd("aeim")
    
    def call_function(self, func_addr, ret_addr, 
                      eax=0, ecx=0, edx=0, ebx=0, esi=0, edi=0):
        """Set registers, emulate from func_addr to ret_addr, return registers."""
        self.r2.cmd("aei; aeim")
        self.r2.cmd(f"ar eip={func_addr}")
        self.r2.cmd(f"ar eax={eax}; ar ecx={ecx}; ar edx={edx}")
        self.r2.cmd(f"ar ebx={ebx}; ar esi={esi}; ar edi={edi}")
        self.r2.cmd(f"aesu {ret_addr}")
        return {
            'eax': int(self.r2.cmd("aer eax").strip(), 16),
            'ecx': int(self.r2.cmd("aer ecx").strip(), 16),
            'edx': int(self.r2.cmd("aer edx").strip(), 16),
            'ebx': int(self.r2.cmd("aer ebx").strip(), 16),
        }
    
    def read_memory(self, addr, size=4):
        out = self.r2.cmd(f"px {size} @ {addr}")
        # parse hex dump
        ...
        return value
```

### Test framework

```python
class SimulatorRef:
    """Mirrors the Python simulator's expected behavior for comparison."""
    
    def rng(self, state):
        s = (state * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        return s, (s >> 16) & 0x7FFF
    
    def aimed_angle(self, bullet_raw_x, bullet_raw_y, player_x, player_y, spread):
        """Octant-based angle computation matching 99.exe."""
        # ... (from 99_reconstructed.c, now ported to Python)
        pass
    
    def spawn_bullet(self, pattern, bounce_limit, rng_state, player_x, player_y):
        """Simulate SpawnBullet output."""
        # ...
        pass

def run_test_suite():
    harness = ESILHarness("raw/99.exe")
    ref = SimulatorRef()
    
    passed = 0
    failed = 0
    
    # --- RNG ---
    for seed in [0, 1, 42, 0x80000000, 0xFFFFFFFF, 0x12345678, 
                 0xDEADBEEF, 0x7FFFFFFF, 0x55555555, 0xAAAAAAAA]:
        esil_state = seed
        ref_state = seed
        for i in range(100):
            harness.set_memory(0x405C00, esil_state)
            regs = harness.call_function(0x402000, 0x40201D)
            esil_out = regs['eax']
            ref_state, ref_out = ref.rng(ref_state)
            if esil_out == ref_out:
                passed += 1
            else:
                failed += 1
                print(f"RNG MISMATCH seed={seed:08X} iter={i}: "
                      f"ESIL={esil_out:04X} REF={ref_out:04X}")
    
    print(f"\nRNG: {passed} passed, {failed} failed")
    
    # --- ComputeAimedAngle ---
    # ... (similar pattern for each test category)
    
    print(f"\nTOTAL: {passed} passed, {failed} failed")
```

### Expected output

```
=== RNG ===
  1000/1000 passed
=== ComputeAimedAngle ===
  72/72 passed
=== SpawnBullet ===
  32/32 passed
=== Bullet Movement ===
  160/160 passed
=== Collision ===
  20/20 passed
=== Graze ===
  15/15 passed
=== Pattern SM ===
  10/10 passed

TOTAL: 1309 passed, 0 failed
```

## Key Constraints

1. ESIL can't handle `timeGetTime` import. For EntityLoop, we write the timestamp
   to `G_CurrentTick` (0x406DA4) in ESIL memory before each call, and set
   `G_NextSpawnTime` and `G_NextPatternTime` to future values to avoid spawn/pattern
   triggers during movement-only tests.

2. ESIL can't handle `BitBlt` (GDI import). The MainFrame function calls BitBlt at the end.
   We emulate up to but not including the rendering code, or we mock the import.

3. VEL_TABLE and ACCEL_TABLE are baked into the binary at fixed addresses.
   ESIL reads them from the binary's data section automatically.

4. The binary is only 27KB — ESIL emulation should be near-instant for individual
   function calls (microseconds each).

## What NOT to do

- ❌ Don't write C code unless ESIL finds a bug that needs documenting
- ❌ Don't emulate the full message loop (WinMain, WindowProc) — not gameplay-relevant
- ❌ Don't emulate rendering functions — GDI state is irrelevant to game logic

## TODOs

1. [x] Create `tools/verify_esil_full.py` — ESILHarness class with set_memory(), call_function(), read_memory()
2. [x] Implement `SimulatorRef` class mirroring hijack_tools/simulator/functions.py for independent reference
3. [x] RNG verification: 10 seeds × 100 iterations → match rng_next() exactly
4. [x] ComputeAimedAngle verification: 8 octants × 3 spreads × 3 distances → match compute_aimed_angle()
5. [x] SpawnBullet verification: 8 patterns × 4 edges → match spawn_bullet()
6. [x] Bullet movement verification: Type 0/1/2/3 × 10 frames → match move_bullet_type*()
7. [x] Collision verification: hitbox edge cases → match check_collision()
8. [x] Graze verification: entry/exit cases → match check_graze_enter() + graze counting
9. [x] Pattern SM verification: pattern transitions → match pattern_update()
10. [x] Run full suite — confirm 1103 validation points all PASS

## Final Verification Wave

F1. [x] Oracle reviews simulator for remaining behavioral gaps vs ANNOTATED.md assembly spec
F2. [x] Run all existing simulator tests (`python3 -m pytest tests/test_functions.py tests/test_integration.py`) — 51/51 pass

## Success Criteria

Every gameplay function's output matches between ESIL and Python simulator.
Any mismatch → fix the simulator → re-run → all green.
Final output: `1300+/1300+ passed, 0 failed`.

## START: `$start-work`
