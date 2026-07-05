# tests/ — Test Suite

**Generated:** 2026-06-30

## OVERVIEW

3-tier test pyramid: unit tests (pure Python) → integration tests (multi-function cycles) → cross-validation (Python vs real `99.exe`). No test framework — custom `run_all()` pattern with raw `assert`. C ground truth binaries for critical functions.

## STRUCTURE

```
tests/
├── test_functions.py        # 30 unit tests — isolated game functions
├── test_integration.py      # 20 integration tests — full frame cycles
├── test_cross_validate.py   # Python vs real 99.exe (Windows only)
├── test_oracle.py           # GameOracle: save/restore state, single-frame step
├── test_angle.c             # C ground truth: aimed angle + RNG (compile: tcc)
├── test_angle.exe           # Compiled C test binary
└── tmp/                     # Temp test artifacts
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| **Run all tests (no binary)** | `python test_functions.py && python test_integration.py` | 50 tests total |
| **Verify Python = real game** | `python test_cross_validate.py` | Requires running 99.exe on Windows |
| **Test a specific function** | `test_functions.py` | 30 unit tests, each testing one game function |
| **Test full frame cycles** | `test_integration.py` | Pattern lifecycle, spawn, collision chains |
| **Regenerate C ground truth** | `tcc test_angle.c -o test_angle.exe` | Requires TCC compiler |
| **Debug simulation accuracy** | `test_oracle.py` | Save/restore game state, step 1 frame, compare |

## CONVENTIONS

1. **`run_all()` pattern**: Each test file has a `run_all()` function with a hardcoded list of test functions. No test discovery, no fixtures.
2. **Raw `assert` only**: No pytest, no unittest. Error messages are f-strings.
3. **No test dependencies**: Test files import directly from `hijack_tools.simulator.*` or `hijack_tools.game_control`.
4. **`if __name__ == "__main__": run_all()`**: Each file is a standalone script.
5. **Test order within file**: Each `run_all()` maintains a manual ordered list of test functions. Not randomized.

## ANTI-PATTERNS

- **DO NOT** skip cross-validation — if Python ≠ real game, AI will make wrong decisions.
- **DO NOT** delete failing tests to "pass" — fixes must bring Python in line with `.asm`.
- **DO NOT** add pytest/unittest without converting ALL tests — mixed frameworks are worse than none.
