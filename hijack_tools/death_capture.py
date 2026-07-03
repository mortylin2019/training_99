"""death_capture.py — Run real game with beam AI, capture death state for analysis."""
import sys, json, time, ctypes, struct

sys.path.insert(0, '.')
from game_control import GameControl
from simulator.c_wrapper import c_beam_search
from ai_beam import BeamAI

g = GameControl()
g.launch_game()
time.sleep(0.5)

# Wait for game to be in playing state
print('Waiting for game to start...')
for i in range(100):
    state = g.get_game_state()
    if g.is_playing() and not g.is_game_over():
        print(f'Game started (state={state})')
        break
    # Press enter to advance screens
    g.press_enter()
    time.sleep(0.2)
else:
    print('Game never started!')
    g.cleanup()
    sys.exit(1)

# Set difficulty NORMAL
g.write_int(0x00406d74, 1)
g.write_int(0x00406d84, 1)
g.write_int(0x00406d90, 1)
g.write_int(0x00406d80, 0)
time.sleep(0.5)

ai = BeamAI()
last_state = None
last_bits = 0
frame = 0

try:
    while g.is_playing() and not g.is_game_over():
        px, py = g.get_player_pos()
        bullets = g.get_bullets()
        active = [b for b in bullets if b.angle_index != 0xFF]

        # Save state before deciding
        last_state = {
            'frame': frame,
            'px': px, 'py': py,
            'bullets': [(b.raw_x, b.raw_y, b.angle_index, b.type,
                         b.timer, b.counter, b.vx, b.vy) for b in active]
        }

        bits = ai.decide(px, py, active)
        last_bits = bits
        g.write_int(0x00406d7c, bits)

        frame += 1
        if frame % 500 == 0:
            print(f'Frame {frame}: alive, {len(active)} bullets')

        time.sleep(0.001)

except Exception as e:
    print(f'Error: {e}')

# Game over - save death context
print(f'DIED at frame {frame}')
print(f'Last bits: {last_bits}')

if last_state:
    with open('death_state.json', 'w') as f:
        json.dump(last_state, f)
    print(f'Saved death state: {len(last_state["bullets"])} bullets')

    # What would simulator's beam search have done?
    px, py = last_state['px'], last_state['py']
    active_sim = [((b[0] >> 6) - 4, (b[1] >> 6) - 4, b[2]) for b in last_state['bullets']]
    alt_bits = c_beam_search(px, py, active_sim)
    print(f'Beam search on death state: {alt_bits} (original: {last_bits})')
    if alt_bits != last_bits:
        print('DIFFERENT! Beam would have chosen another move!')

    # Check if any bullet was hitting the player
    for b in last_state['bullets']:
        bx = (b[0] >> 6) - 4
        by = (b[1] >> 6) - 4
        if abs(bx - px) < 13 and abs(by - py) < 10:
            print(f'DEATH: Bullet at ({bx},{by}) type={b[3]} ang={b[2]} hitting player at ({px},{py})')

g.write_int(0x00406d7c, 0)
g.cleanup()
