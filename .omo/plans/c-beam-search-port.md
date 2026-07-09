# Plan: Safe Beam Search Port to C

## Safety Principle

The Python JIT beam search is proven (1105/1105 ESIL tests, 42.9s avg survival). The C port MUST produce identical output for identical input. Every step has a verification gate — no gate passes, no proceed.

## Gate 0: Establish Ground Truth

**Goal**: Capture Python beam search output for a diverse set of game states, so we can compare C output against it.

1. Write `tools/capture_beam_truth.py`:
   - Run simulator for N seeds (N=100), difficulty=1
   - At each frame where AI decides, record: `(px, py, bullet_xy_angles, beam_output_bits)`
   - Save as `tests/beam_truth.npz` (compressed, ~5-10MB for 100 seeds)
   - This is our immutable reference — C must match EVERY entry

**Gate**: File produced with >10,000 recorded decisions.

## Gate 1: Implement C Beam Search

**Goal**: Port `_beam_search` function from `ai_beam.py` to `c_engine.c`.

1. Study the Python JIT `_beam_search` function line-by-line:
   - Beam state: `beam_px[K]`, `beam_py[K]`, `beam_first[K]`, `beam_score[K]`
   - Expand loop: K beam elements × 9 moves × D depth
   - Scoring: `_score_pos` (collision + danger + center + wall)
   - Time weighting: `w = 1/(base + t*rate)`
   - Tiebreak: `((int(nx*7919) ^ int(ny*6271)) & 0xFFF) * 1e-6`
   - Intermediate frame checking between beam steps

2. Write `c_beam_search(px, py, bullet_count, bullet_xs, bullet_ys, bullet_angles, vel_table)` in `c_engine.c`

3. Key implementation notes:
   - Use `double` for all floating point (matches Python `float64`)
   - Use `int32_t` for indices
   - Inline `_score_pos` logic directly (function call overhead matters)
   - Match MOVES array exactly (Python list order)
   - Match all constant values from `algo_config.py`

**Gate**: C code compiles with `gcc -O2 -Wall -Werror -shared -fPIC -o sim_core.so c_engine.c`

## Gate 2: Unit Test — Single Frame Identity

**Goal**: For ONE game state, C beam search returns same move as Python.

1. Write `tests/test_c_beam_unit.py`:
   - Load beam_truth.npz
   - For the first 100 entries, call both Python `_beam_search` and C `c_beam_search`
   - Assert: `py_bits == c_bits` for ALL 100 entries
   - Print diff for any mismatch

**Gate**: 100/100 matches. If any mismatch: debug C with side-by-side print of intermediate beam states.

## Gate 3: Exhaustive Cross-Validation

**Goal**: C matches Python for ALL recorded game states.

1. Run `tests/test_c_beam_unit.py` on full beam_truth.npz (all 10,000+ entries)
2. Assert: 100% identical output

**Gate**: 10,000+/10,000+ matches. Zero failures allowed.

## Gate 4: Simulator Survival Parity

**Goal**: C beam search produces identical survival times as Python on the simulator.

1. Modify `simulator/runner.py` to support `--engine c` vs `--engine python`
2. Run benchmark: 50 seeds, difficulty=1, both engines
3. Assert: survival times are identical (deterministic, same RNG seed)

**Gate**: All 50 survival times match exactly between Python and C.

## Gate 5: Enable C Engine (Guarded)

**Goal**: Switch live runner to use C beam search.

1. Set `USE_C_BEAM = True` in `algo_config.py`
2. Verify `ai_beam.py`'s C engine path works with the new `c_beam_search`
3. Run 10 seeds on simulator → confirm identical results
4. Run 5 runs on live game → check LAG disappears

**Gate**: Zero LAG on live game, identical survival to Python beam.

## Gate 6: Remove Dead Code

**Goal**: Delete Python JIT beam search, numba dependency.

1. Remove `_beam_search`, `_score_pos`, `_max_gap_move`, `_mc_search` from `ai_beam.py`
2. Remove `from numba import njit` — verify nothing else needs it
3. Remove `simulator/jit_core.py` — verify no remaining imports
4. Remove `numba` from requirements
5. Run full test suite: `test_functions.py`, `test_integration.py`
6. Run AI benchmark on simulator: verify unchanged

**Gate**: All tests pass, benchmark identical.

## Rollback Plan

If any gate fails:
1. Keep Python JIT code as fallback
2. `USE_C_BEAM = False` — run existing proven path
3. Debug C version against Python version step-by-step with intermediate dumps

## Files Created / Modified

| File | Action |
|---|---|
| `tools/capture_beam_truth.py` | NEW — ground truth capture |
| `tests/beam_truth.npz` | NEW — reference data (~5-10MB, gitignored) |
| `tests/test_c_beam_unit.py` | NEW — C vs Python comparison test |
| `hijack_tools/simulator/c_engine.c` | MODIFY — add `c_beam_search` |
| `hijack_tools/simulator/c_wrapper.py` | MODIFY — add Python binding |
| `hijack_tools/ai_beam.py` | MODIFY — call C path when available |
| `hijack_tools/algo_config.py` | MODIFY — enable `USE_C_BEAM` after gates pass |
