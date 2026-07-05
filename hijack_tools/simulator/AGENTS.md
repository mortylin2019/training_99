# simulator/ — Deterministic 99.exe Replica

**Generated:** 2026-06-30

## OVERVIEW

Faithful offline game engine. Pure Python implementation matching the real `99.exe` exactly — same RNG, velocity tables, bullet physics, collision, pattern state machine. Used for AI benchmarking without the live game binary.

## STRUCTURE

```
simulator/
├── engine.py           # GameSimulator: orchestrates all subsystems (205 loc)
├── functions.py        # Assembly-verified C reimplementations (455 loc)
├── bullet.py           # Bullet entity + move_bullet() logic
├── tables.py           # VEL_TABLE, ACCEL_TABLE (64-angle lookup)
├── rng.py              # LCG: state = state*0x343FD+0x269EC3
├── config.py           # All game constants (duplicated in config.yaml)
├── config.yaml         # Same constants in YAML format
├── jit_core.py         # Numba JIT-compiled core (243 loc)
├── c_wrapper.py        # Python ctypes wrapper for sim_core.dll (299 loc)
├── c_engine.c          # C engine source
├── sim_core.dll        # Compiled C engine (benchmarks)
├── sim_core.def        # DLL export definitions
├── runner.py           # Batch AI benchmarking via ProcessPool
├── extract_tables.py   # Extract velocity tables from live 99.exe
└── __init__.py         # Package init (imports engine, bullet, config)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| **Change game constants** | `config.py` + `config.yaml` | Change BOTH. Verified against decompiled C. |
| **Fix bullet physics** | `functions.py` | Assembly-verified C function reimplementations |
| **Fix RNG** | `rng.py` | Must match game's LCG exactly |
| **Fix entity lifecycle** | `engine.py` | Full frame cycle: spawn → move → collide → graze → pattern FSM |
| **Speed up simulation** | `jit_core.py` or `c_wrapper.py` | Numba JIT or C DLL for hot paths |
| **Add new bullet type** | `functions.py` + `config.py` | Match decompiled C behavior exactly |
| **Benchmark AI** | `runner.py --ai ai_beam --runs 500` | ProcessPool, tqdm progress |
| **Extract game tables** | `extract_tables.py` | Requires running 99.exe (reads live memory) |

## CONVENTIONS

1. **Dual config**: `config.py` and `config.yaml` MUST stay in sync. Change both.
2. **Assembly-verified**: Every function in `functions.py` verified against `.asm` (NOT decompiled C).
3. **Relative imports**: Internal imports use `from .engine import ...` (proper package structure).
4. **Type hints used**: Primitive types only (`int`, `float`, `list[Bullet]`).
5. **Config namespace**: All constants accessed as `config.PLAYER_X_MAX`, etc.

## ANTI-PATTERNS

- **DO NOT** trust decompiled C — verify against `.asm`. The C code has Ghidra artifacts (variable swaps, uninitialized variables).
- **DO NOT** change config.py without config.yaml (or vice versa).
- **DO NOT** call Type 2 "bounce" — it's Homing-Acceleration. Variable `bounce_limit` is legacy terminology.
- **DO NOT** change RNG constants — the LCG (`0x343FD`, `0x269EC3`) must match the game exactly.
