"""Worker function for parallel beam search benchmarks."""
import sys, os
# Ensure hijack_tools is importable from any working directory
_dir = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_dir)
if _parent not in sys.path:
    sys.path.insert(0, _parent)
from simulator.c_wrapper import CSimulator


def test_seed(args):
    """Run one seed on C simulator. Returns (diff, seed, survival_s)."""
    diff, seed = args
    cs = CSimulator(diff, seed)
    for _ in range(50):  # warmup
        cs.step(0)
    for f in range(8000):
        bits = cs.beam_search()
        if not cs.step(bits):
            return diff, seed, f / 80.0
    return diff, seed, 100.0
