#!/usr/bin/env python3
"""
Gate 2+3: Verify C beam search matches Python output on beam_truth.npz.

Usage:
  python tests/test_c_beam_unit.py          # first 100 entries (Gate 2)
  python tests/test_c_beam_unit.py --full   # all entries (Gate 3)
"""
import sys, os, argparse, ctypes
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hijack_tools'))

# Python beam search
from hijack_tools.ai_beam import BeamAI, _beam_search
from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE

# Load C shared library
so_path = os.path.join(os.path.dirname(__file__), '..', 'hijack_tools', 'simulator', 'sim_core.so')
lib = ctypes.CDLL(so_path)

lib.sim_beam_search_raw.argtypes = [
    ctypes.c_int, ctypes.c_int,           # px, py
    ctypes.c_int,                          # n_bullets
    ctypes.POINTER(ctypes.c_int),          # bullet_xs
    ctypes.POINTER(ctypes.c_int),          # bullet_ys
    ctypes.POINTER(ctypes.c_int),          # bullet_angles
]
lib.sim_beam_search_raw.restype = ctypes.c_int


def python_beam(px, py, bullets):
    """Call Python _beam_search with precomputed paths."""
    ai = BeamAI(vel_table=VEL_TABLE, accel_table=ACCEL_TABLE)
    paths = ai._predict(bullets)
    idx = int(_beam_search(float(px), float(py), paths))
    return idx


def c_beam(px, py, xs, ys, angles):
    """Call C sim_beam_search_raw via ctypes."""
    n = len(xs)
    bx_arr = (ctypes.c_int * n)(*[int(x) for x in xs])
    by_arr = (ctypes.c_int * n)(*[int(y) for y in ys])
    ang_arr = (ctypes.c_int * n)(*[int(a) for a in angles])
    bits = lib.sim_beam_search_raw(px, py, n, bx_arr, by_arr, ang_arr)
    # Map bits back to move index (0-8)
    BITS = [0, 1, 8, 2, 4, 3, 5, 10, 12]
    for i, b in enumerate(BITS):
        if b == bits:
            return i
    return -1


def test(data_path, max_samples=None):
    """Compare Python vs C beam search."""
    data = np.load(data_path)
    n = len(data['px'])
    if max_samples:
        n = min(n, max_samples)

    matches = 0
    mismatches = []
    pbar = None
    try:
        from tqdm import tqdm
        pbar = tqdm(range(n), desc="Testing")
    except ImportError:
        pass

    for i in (pbar or range(n)):
        px = int(data['px'][i])
        py = int(data['py'][i])
        nb = int(data['n_bullets'][i])
        offset = int(data['bullet_offsets'][i])

        xs = data['bullet_xs'][offset:offset + nb]
        ys = data['bullet_ys'][offset:offset + nb]
        angles = data['bullet_angles'][offset:offset + nb]

        py_result = data['beam_idx'][i]  # ground truth from capture

        # C result
        c_result = c_beam(px, py, xs, ys, angles)

        if c_result == py_result:
            matches += 1
        else:
            mismatches.append((i, px, py, nb, py_result, c_result))
            if pbar:
                pbar.set_postfix(match=f"{matches}/{i+1}", mismatches=len(mismatches))

    print(f"\nResults: {matches}/{n} match ({100.0 * matches / n:.1f}%)")
    if mismatches:
        print(f"Mismatches: {len(mismatches)}")
        for i, px, py, nb, py_r, c_r in mismatches[:10]:
            print(f"  [{i}] px={px} py={py} nb={nb}  Python={py_r}  C={c_r}")
        if len(mismatches) > 10:
            print(f"  ... and {len(mismatches) - 10} more")

    return matches == n


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="tests/beam_truth.npz")
    p.add_argument("--full", action="store_true")
    p.add_argument("--max", type=int, default=None)
    args = p.parse_args()

    if not os.path.exists(args.data):
        print(f"Missing: {args.data}")
        print("Run: python tools/capture_beam_truth.py --seeds 30")
        sys.exit(1)

    max_n = None if args.full else (args.max or 100)
    label = f"first {max_n}" if max_n else "ALL"
    print(f"Testing C beam search vs Python ({label} entries)...")
    ok = test(args.data, max_samples=max_n)
    if ok:
        print("\n✓ PASS — C matches Python exactly")
    else:
        print("\n✗ FAIL — C output differs from Python")
        sys.exit(1)
