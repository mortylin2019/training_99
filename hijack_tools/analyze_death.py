"""Analyze death snapshot."""
import json, sys
sys.path.insert(0, '.')
from simulator.c_wrapper import c_beam_search

with open('../logs/death_r1.json') as f:
    state = json.load(f)

px, py = state['px'], state['py']
bullets_raw = state['bullets']

print(f'Player at ({px}, {py})')
print(f'{len(bullets_raw)} bullets')
print(f'Original bits: {state["bits"]}')

# Count types
types = {}
for b in bullets_raw:
    t = b[3]
    types[t] = types.get(t, 0) + 1
print(f'Types: {types}')

# Convert to beam format (pixel coords + angle)
active = [((b[0] >> 6) - 4, (b[1] >> 6) - 4, b[2]) for b in bullets_raw]

# Run beam search
bits = c_beam_search(px, py, active)
print(f'Beam search result: {bits}')
if bits != state['bits']:
    print('DIFFERENT! Beam would have chosen another move!')

# Check collisions
for b in bullets_raw:
    bx = (b[0] >> 6) - 4
    by = (b[1] >> 6) - 4
    if 2 <= bx - px < 13 and 0 <= by - py < 10:
        print(f'COLLISION: bullet at ({bx},{by}) type={b[3]} ang={b[2]}')
