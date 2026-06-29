"""replay_test.py — Capture real game state, replay in simulator, compare survival."""
import sys, json, time, ctypes
sys.path.insert(0, '.')
from game_control import GameControl
from ai_beam import BeamAI
from simulator.c_wrapper import CSimulator, _lib, c_beam_search

# ── Launch real game and start beam AI ──
g = GameControl()
g.launch_game()
time.sleep(0.5)

# Auto-advance to playing state
for _ in range(20):
    state = g.get_game_state()
    if g.is_playing() and not g.is_game_over():
        print(f'Game started (state={state})')
        break
    g.press_enter()
    time.sleep(0.2)
else:
    print('Failed to start game')
    g.cleanup()
    sys.exit(1)

g.write_int(0x00406d74, 1)
g.write_int(0x00406d84, 1)
g.write_int(0x00406d90, 1)
g.write_int(0x00406d80, 0)
time.sleep(0.5)

ai = BeamAI()
captured_state = None
real_death_frame = None
frame = 0

print('Running real game with beam AI...')
try:
    while g.is_playing() and not g.is_game_over():
        px, py = g.get_player_pos()
        bullets = g.get_bullets()
        active = [b for b in bullets if b.angle_index != 0xFF]

        # Capture state at ~400 frames (~5s)
        if frame == 400 and not captured_state:
            # Read timing values
            cur_time = g.read_int(0x00406da4)  # timeGetTime() at entity loop start
            next_pat_raw = g.read_int(0x00406e00)
            next_spawn_raw = g.read_int(0x00406dfc)
            
            # Convert from absolute timeGetTime to relative frame offsets
            # At 80 FPS: 1 frame = 12.5ms, so offset_frames ≈ (abs_time - cur_time) / 12.5
            # But the simulator uses frames directly, so convert ms to frames
            ms_per_frame = 1000.0 / 80.0  # 12.5ms
            next_pat_offset = max(0, (next_pat_raw - cur_time) / ms_per_frame)
            next_spawn_offset = max(0, (next_spawn_raw - cur_time) / ms_per_frame)
            
            captured_state = {
                'frame': frame,
                'px': px, 'py': py,
                'bullets': [(b.raw_x, b.raw_y, b.angle_index, b.type,
                             b.timer, b.index, b.vx, b.vy) for b in active],
                'rng': g.read_int(0x00405c00),
                'pattern': g.read_int(0x00406dbc),
                'next_pattern': int(next_pat_offset),  # frames from now
                'next_spawn': int(next_spawn_offset),  # frames from now
                'bullet_count': g.read_int(0x00406da8),
                'cur_time': cur_time,
            }
            print(f'Captured state at frame {frame}: {len(active)} bullets')
            print(f'  Pattern={captured_state["pattern"]} next_pat_offset={next_pat_offset:.0f}frames')
            print(f'  RNG={captured_state["rng"]:#x}')

        bits = ai.decide(px, py, active)
        g.write_int(0x00406d7c, bits)
        frame += 1
        time.sleep(0.001)

except Exception as e:
    print(f'Error: {e}')

real_death_frame = frame if (g.is_game_over() or not g.is_playing()) else None
real_survival = real_death_frame / 80.0 if real_death_frame else None
print(f'Real game died at frame {real_death_frame} ({real_survival:.1f}s)' if real_survival else 'Game still alive')
g.write_int(0x00406d7c, 0)
g.cleanup()

# ── Replay in simulator ──
if captured_state:
    print('\n--- Replaying in simulator ---')
    cs = CSimulator(1, 42)  # seed doesn't matter — we load state

    # Load captured state with precise timing sync
    # The simulator uses frame-based timing. Convert offsets to absolute frame numbers.
    cap_frame = captured_state['frame']
    abs_next_pat = cap_frame + captured_state['next_pattern']
    abs_next_spawn = cap_frame + captured_state['next_spawn']
    
    cs.set_player(captured_state['px'], captured_state['py'])
    cs.set_rng(captured_state['rng'])
    cs.set_frame(cap_frame)  # sync frame counter
    cs.set_next_spawn(abs_next_spawn)  # sync spawn timer
    cs.set_pattern(captured_state['pattern'], abs_next_pat)
    cs.load_bullets(captured_state['bullets'])
    
    print(f'Simulator loaded: px={cs.px}, py={cs.py}, bullets={_lib.sim_get_bullet_count(cs._ptr)}')
    print(f'  frame={cap_frame} RNG={_lib.sim_get_rng(cs._ptr):#x}')
    print(f'  pattern={captured_state["pattern"]} next_pat={abs_next_pat} (in {captured_state["next_pattern"]}f)')
    print(f'  next_spawn={abs_next_spawn} (in {captured_state["next_spawn"]}f)')

    # Run simulator with beam search from this state
    # Apply 1-frame delay to match real game's measurement-to-action timing
    sim_frame = 0
    sim_survival = 100.0
    prev_bits = 0
    for f in range(8000 - captured_state['frame']):
        bits = cs.beam_search()
        if not cs.step(prev_bits):
            sim_survival = captured_state['frame'] / 80.0 + sim_frame / 80.0
            print(f'Simulator DIED at frame {cs.frame} (total ~{sim_survival:.1f}s)')
            break
        prev_bits = bits
        sim_frame += 1
    else:
        print(f'Simulator SURVIVED 100s CAP!')

    if real_survival:
        print(f'\nComparison: Real={real_survival:.1f}s  Sim={sim_survival:.1f}s')
