"""Compare first 10 frames after capture between real and simulator."""
import json, sys
sys.path.insert(0, '.')
from simulator.c_wrapper import CSimulator, _lib, c_beam_search

with open('../logs/death_r1.json') as f:
    state = json.load(f)

px, py = state['px'], state['py']
print(f'Death state: player=({px},{py}) bits={state["bits"]}')
print(f'Bullets: {len(state["bullets"])}')

# Test beam determinism
active = [((b[0]>>6)-4, (b[1]>>6)-4, b[2]) for b in state['bullets']]
r1 = c_beam_search(px, py, active)
r2 = c_beam_search(px, py, active)
print(f'Beam deterministic: {r1 == r2} (both={r1})')

# Check movement
bits = state['bits']
dx = (1 if (bits & 8) else 0) - (1 if (bits & 1) else 0)
dy = (1 if (bits & 4) else 0) - (1 if (bits & 2) else 0)
print(f'Move: bits={bits} -> ({dx},{dy}) -> next pos ({px+dx},{py+dy})')

# Check collision at the original state
for b in state['bullets']:
    bx = (b[0]>>6)-4
    by = (b[1]>>6)-4
    if 2 <= bx-px < 13 and 0 <= by-py < 10:
        print(f'COLLISION: bullet at ({bx},{by}) type={b[3]} ang={b[2]}')
