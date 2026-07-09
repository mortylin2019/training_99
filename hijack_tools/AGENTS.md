# hijack_tools/ — AI Bots & Game Interface

**Generated:** 2026-06-30

## OVERVIEW

Python bots that hijack the live `99.exe` process via `ReadProcessMemory`/`WriteProcessMemory`, read bullet positions, and play autonomously via input bitmask writes. Includes 3 AI algorithms + a deterministic offline simulator.

## STRUCTURE

```
hijack_tools/
├── game_control.py      # Process I/O: launch, memory r/w, game state (521 loc)
├── runner.py            # Main AI runner entry point
├── multi_runner.py      # Parallel multi-instance runner
├── ai_basic.py          # AI: 1/r² repulsion baseline
├── ai_beam.py           # AI: JIT Beam Search with C DLL fallback
├── ai_nn.py             # AI: NN-boosted beam search + MCTS variants
├── bullet_data.py       # Bullet @dataclass (shared data model)
├── keyboard.py          # Direction bitmask → name mapping
├── algo_config.py       # Beam search config constants
├── profile_ai.py        # cProfile AI benchmark
├── bench_worker.py      # C engine benchmark worker
├── analyze_death.py     # Death analysis tool
├── death_capture.py     # Death capture tool
├── measure_spawn.py     # Spawn measurement tool
├── input_test.py        # Input hijack testing
├── replay_test.py       # Capture/replay comparison
├── verify_determinism.py # Determinism verification
└── simulator/           # Offline game engine replica (see simulator/AGENTS.md)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| **Add new AI** | Create new file, import in `runner.py` | Pattern: `class MyAI: decide(px, py, bullets) → bitmask` |
| **Change AI algorithm** | `ai_beam.py` (406 loc) or `ai_nn.py` (390 loc) | Pure functions — no I/O, no process access |
| **Fix memory access** | `game_control.py` | ONLY module touching live process memory |
| **Change beam search params** | `algo_config.py` | Depth, width, scoring weights, toggles |
| **Debug AI decisions** | `profile_ai.py` | cProfile with fake bullets |
| **Add new bullet type** | `bullet_data.py` | Shared @dataclass |
| **Run AI** | `runner.py --ai ai_beam --runs 10` | Real game required |
| **Benchmark offline** | `simulator/runner.py --ai ai_beam --runs 500` | No game needed |

## CONVENTIONS

1. **Import pattern**: ALL modules use dual-path import:
   ```python
   try:
       from game_control import GameControl
   except ImportError:
       from hijack_tools.game_control import GameControl
   ```
2. **Logging**: `loguru` only — `from loguru import logger`. Setup: `logger.remove()` + `logger.add(sys.stderr, ...)`.
3. **Input bitmask hijack**: Write to `0x00406d7c`. NEVER `SendMessage` for movement. NEVER direct position write (`0x00406d6c`).
4. **STOP on exit**: Always `write_int(0x00406d7c, 0)` before exiting.
5. **Bullet filtering**: Always `[b for b in bullets if b.angle_index != 0xFF]`.
6. **AI algorithms are pure**: State in → bitmask out. No process access, no file I/O.

## ANTI-PATTERNS

- **DO NOT** write to `0x00406d6c` (player X) — teleport cheating
- **DO NOT** use `send_key()` for gameplay movement — slow/unreliable
- **DO NOT** use `print()` — use `loguru`
- **DO NOT** use raw `ctypes` for memory access — go through `GameControl.read_int()`/`write_int()`
- **DO NOT** call Type 2 bullets "bounce" — they are Homing-Acceleration
- **DO NOT** trust decompiled C over assembly — `.asm` is authoritative
