"""Measure real game spawn rate."""
import sys, time, ctypes
sys.path.insert(0, '.')
from game_control import GameControl

g = GameControl()
g.launch_game()
time.sleep(0.5)

for _ in range(10):
    g.press_enter()
    time.sleep(0.2)
    if g.is_playing():
        break

if not g.is_playing():
    print('Game not playing')
    g.cleanup()
    exit()

g.write_int(0x00406d74, 1)
g.write_int(0x00406d84, 1)
g.write_int(0x00406d90, 1)
g.write_int(0x00406d80, 0)
time.sleep(0.5)

# Measure bullet count over time
last_count = g.read_int(0x00406da8)
t0 = time.time()
print(f'Start: {last_count} bullets')

for i in range(30):
    time.sleep(1.0)
    count = g.read_int(0x00406da8)
    if count != last_count:
        t = time.time() - t0
        print(f't={t:.1f}s: {count} bullets (+{count - last_count})')
        last_count = count

# Read spawn timing
ns = g.read_int(0x00406dfc)
ct = g.read_int(0x00406da4)
print(f'next_spawn={ns}, current_time={ct}')
if ns > ct:
    print(f'Spawn in: {(ns - ct)}ms')

g.write_int(0x00406d7c, 0)
g.cleanup()
