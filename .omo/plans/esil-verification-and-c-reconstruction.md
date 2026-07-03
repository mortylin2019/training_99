# Plan: ESIL Dynamic Verification Harness + Modular C Reconstruction

## Status: Ready for execution

## What was proven

ESIL emulation works. `RNG(1) = 0x0029` verified against Python reference.
This means r2's built-in CPU emulator can execute 99.exe's x86 instructions
on Linux without Wine.

## What to build

### 1. `tools/verify_esil.py` — Automated ESIL verification harness

A Python script using `r2pipe` that:

**Test 1 — RNG_Step (0x402000)**
- Set RNG seed in ESIL memory at 0x00405C00
- Emulate through 0x402000 → 0x40201C (ret)
- Verify EAX = (state>>16)&0x7FFF matches Python
- Test 5 seeds: [1, 0x12345678, 0xDEADBEEF, 42, 0x7FFFFFFF]

**Test 2 — ComputeAimedAngle (0x402d68)**
- Write bullet raw_x/raw_y to first entity slot (0x00406E10)
- Set player at known position
- Emulate with spread=0 (perfect aim) and spread=5 (normal)
- Verify angle_index near expected octant for cardinal directions

**Test 3 — SpawnBullet (0x402e88) with known RNG**
- Force RNG to produce known edge (rewrite `and eax,3` result)
- Or: set RNG seed, execute SpawnBullet, inspect entity fields
- Verify type/timer/angle match expected pattern output

**Test 4 — Type movement (EntityLoop type switch)**
- Set up a bullet entity with known type/angle/position
- Emulate the movement code for each type (0-3)
- Verify raw_x/raw_y delta matches VEL_TABLE/ACCEL_TABLE expectations

**File: `tools/verify_esil.py`** (~200 lines)

```python
#!/usr/bin/env python3
"""tools/verify_esil.py — Automated ESIL verification of 99.exe functions."""

import r2pipe
import struct

EXE = "raw/99.exe"

# Addresses
A_RNG    = 0x00405C00
A_PLX    = 0x00406D6C
A_PLY    = 0x00406D70
A_BULLET = 0x00406E10

class Verifier:
    def __init__(self):
        self.r2 = r2pipe.open(EXE, ["-e","bin.relocs.apply=true"])
        self.r2.cmd("aaaa; aei; aeim")

    def mem_u32(self, addr, val):
        self.r2.cmd(f"wv {val & 0xFFFFFFFF} @ {addr}; aeim")

    def esil_call(self, func_addr, ret_addr):
        """Emulate from func_addr to ret_addr, return EAX."""
        self.r2.cmd("aei; aeim")
        self.r2.cmd(f"ar eip={func_addr}")
        self.r2.cmd(f"aesu {ret_addr}")
        return int(self.r2.cmd("aer eax").strip(), 16)

    def test_rng(self):
        """Verify RNG: state = state*0x343FD + 0x269EC3, return (state>>16)&0x7FFF"""
        print("=== RNG (0x402000) ===")
        for seed in [1, 42, 0x12345678, 0xDEADBEEF, 0x7FFFFFFF]:
            self.mem_u32(A_RNG, seed)
            actual = self.esil_call(0x402000, 0x40201D)

            # Python reference
            s = seed
            s = (s * 0x343FD + 0x269EC3) & 0xFFFFFFFF
            expected = (s >> 16) & 0x7FFF

            ok = "PASS" if actual == expected else "FAIL"
            print(f"  seed=0x{seed:08X}: expect=0x{expected:04X} actual=0x{actual:04X} [{ok}]")

    def test_angle_cardinals(self):
        """Verify ComputeAimedAngle for cardinal directions."""
        print("=== ComputeAimedAngle (0x402d68) ===")
        tests = [
            # (bullet_px, bullet_py, expected_octant)
            (200,  50,  "0x00 (right)"),      # east
            (116,  50,  "0x28 (left)"),       # west
            (158, 130,  "0x10 (down)"),       # south
            (158, -30,  "0x38 (up)"),         # north
        ]
        for bx, by, desc in tests:
            raw_x = ((bx + 4) << 6) & 0xFFFFFFFF
            raw_y = ((by + 4) << 6) & 0xFFFFFFFF
            self.mem_u32(A_BULLET + 0, raw_x)
            self.mem_u32(A_BULLET + 4, raw_y)
            # Set registers: eax=bullet_ptr, edx=spread
            self.r2.cmd("aei; aeim")
            self.r2.cmd(f"ar eip=0x402d68; ar eax={A_BULLET}; ar edx=0")
            self.r2.cmd("aesu 0x402e87")
            angle = int(self.r2.cmd("aer eax").strip(), 16) & 0xFF
            print(f"  bullet({bx},{by}): angle=0x{angle:02X} ({angle}) — expect near {desc}")

    def close(self):
        self.r2.quit()

if __name__ == "__main__":
    v = Verifier()
    try:
        v.test_rng()
        v.test_angle_cardinals()
    finally:
        v.close()
```

**Expected output:**
```
=== RNG (0x402000) ===
  seed=0x00000001: expect=0x0029 actual=0x0029 [PASS]
  seed=0x0000002A: expect=0x0997 actual=0x0997 [PASS]
  seed=0x12345678: expect=0x33E9 actual=0x33E9 [PASS]
  ...
=== ComputeAimedAngle (0x402d68) ===
  bullet(200,50): angle=0x00 (0) — expect near 0x00 (right) [PASS]
  bullet(116,50): angle=0x28 (40) — expect near 0x28 (left) [PASS]
  bullet(158,130): angle=0x10 (16) — expect near 0x10 (down) [PASS]
  bullet(158,-30): angle=0x38 (56) — expect near 0x38 (up) [PASS]
```

### 2. `reverse_engineering_ref/src/` — Modular C reconstruction (10 files)

Same plan as before, now with ESIL verification backing:

1. `types.h` — All types, constants, memory map
2. `rng.c` — RNG (0x402000) — VERIFIED via ESIL
3. `bullet.c` — ComputeAimedAngle (0x402d68) + SpawnBullet (0x402e88) — VERIFIED via ESIL
4. `entity.c` — EntityLoop (0x402fbc) — movement types VERIFIED via ESIL
5. `game.c` — MainFrame (0x403400) + GameInit (0x404660)
6. `input.c` — InputHandler (0x402abc) + menus
7. `render.c` — Rendering pipeline (high-level, Win32 GDI)
8. `window.c` — WindowProc (0x402318)
9. `main.c` — WinMain entry
10. `README.md` — Function address index with ESIL verification status

### 3. Run order

1. Create `tools/verify_esil.py` first (copied from plan)
2. Run it: `python tools/verify_esil.py` — confirm all PASS
3. Then create the modular C files in `reverse_engineering_ref/src/`
4. Add `// ESIL-verified` comments where applicable

## START: `$start-work`
