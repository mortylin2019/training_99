"""
simulator/rng.py - LCG RNG matching game's FUN_00402000 (Util_Random) exactly.
"""
from .config import LCG_MULT, LCG_ADD, LCG_MASK


class LCG:
    def __init__(self, seed=0):
        self.state = seed & 0xFFFFFFFF

    def seed(self, s):
        self.state = s & 0xFFFFFFFF

    def next(self):
        self.state = (self.state * LCG_MULT + LCG_ADD) & 0xFFFFFFFF
        return (self.state >> 16) & LCG_MASK
