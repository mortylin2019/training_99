"""
simulator - Fast, faithful 99.exe simulator for AI testing.

Matches decompiled C: real tables, 4 bullet types, 7 patterns,
exact RNG, correct hitbox + graze. Process-pool parallel.

Usage:
    python -m hijack_tools.simulator.runner --ai ai_beam --runs 500
    python hijack_tools/simulator/extract_tables.py
"""
from .engine import GameSimulator
