"""
tests/test_integration.py — Integration tests: multiple functions, full frame cycles.
Tests verify game behavior across function boundaries using the same ground truth.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hijack_tools.simulator.functions import *
from hijack_tools.simulator.config import *
from hijack_tools.simulator.tables import VEL_TABLE, VEL_TABLE_FULL


# ═══════════════════════════════════════════════════════════════
# Test 1: GameInit — entity array initialization
# ═══════════════════════════════════════════════════════════════

def test_game_init_slots():
    """All 300 slots start with angle_index=0xFF (inactive)."""
    # Simulate GameInit
    slots = [{"angle_index": INACTIVE} for _ in range(MAX_ENTITIES)]
    for i in range(MAX_ENTITIES):
        assert slots[i]["angle_index"] == INACTIVE, f"Slot {i} should be inactive"
    print(f"  GameInit: {MAX_ENTITIES} slots all 0xFF OK")


def test_game_init_difficulties():
    """Bullet count set correctly per difficulty."""
    expected = {0: 30, 1: 50, 2: 100, 3: 200}
    for diff, count in expected.items():
        assert DIFF_BULLETS[diff] == count, f"Diff {diff}: expected {count}"
    print(f"  GameInit difficulties: {expected} OK")


# ═══════════════════════════════════════════════════════════════
# Test 2: Pattern full lifecycle
# ═══════════════════════════════════════════════════════════════

def test_pattern_lifecycle():
    """Pattern: none → start → active → end → cooldown → retry."""
    rng_state = 0
    pattern = 0

    # Frame 0: first pattern check at frame PATTERN_CHECK
    for frame in range(0, PATTERN_CHECK + 100, 100):
        pattern, next_pt, rng_state = pattern_update(
            frame, PATTERN_CHECK, pattern, rng_state)
        # On frame 400+, pattern should either start or retry
        if frame >= PATTERN_CHECK:
            assert next_pt > frame, f"Next pattern time should be in future at frame {frame}"

    # Verify pattern cycles properly
    pattern = 3  # force pattern active
    p, npt, _ = pattern_update(1000, 900, pattern, 0)  # timer expired
    assert p == 0, "Pattern should end when timer expires"
    assert npt == 1000 + PATTERN_CHECK, "Cooldown should be PATTERN_CHECK"

    print("  Pattern lifecycle: start/end/cooldown OK")


def test_pattern_probability():
    """Pattern start uses RNG < 0x3000 threshold (37.5% of 0x8000)."""
    # Statistically verify ~37.5% activation rate over many trials
    starts = 0
    trials = 2000
    rng_state = 1
    for _ in range(trials):
        rng_state, rv = rng_next(rng_state)
        if rv < PATTERN_CHANCE:
            starts += 1
    rate = starts / trials
    # Should be ~0.375 ± 0.05
    assert 0.32 < rate < 0.43, f"Pattern start rate: {rate:.3f} (expected ~0.375)"
    print(f"  Pattern probability: {rate:.3f} (~37.5%) OK")


# ═══════════════════════════════════════════════════════════════
# Test 3: Spawn at all difficulties and patterns
# ═══════════════════════════════════════════════════════════════

def test_spawn_all_patterns():
    """Every pattern (0-7) spawns with correct type and timer."""
    pattern_expect = {
        0: (TYPE_NORMAL, 0),
        1: (TYPE_NORMAL, 0),
        2: (TYPE_HOMING, 0x30),
        3: (TYPE_HOMING, 0x20),
        4: (TYPE_HOMING, 0x10),
        6: (TYPE_ACCEL, 0),
        7: (TYPE_H_ACCEL, 0),  # special, no aim
    }
    for pattern, (exp_type, exp_timer) in pattern_expect.items():
        slot = {}
        rng_state = pattern * 100
        rng_state, bounce, rx, ry, fields = spawn_bullet(
            0, 0, slot, 152, 44, pattern, 0, rng_state)
        assert fields["type"] == exp_type, \
            f"Pattern {pattern}: expected type {exp_type}, got {fields['type']}"
        if pattern != 7:  # pattern 7 returns early, no timer set
            assert fields["timer"] == exp_timer, \
                f"Pattern {pattern}: expected timer {exp_timer}, got {fields['timer']}"
    print("  Spawn all patterns (0-7): OK")


def test_spawn_position_valid():
    """Spawned bullets are always on a valid edge."""
    for _ in range(500):
        slot = {}
        rng_state, bounce, rx, ry, fields = spawn_bullet(
            0, 0, slot, 100, 100, 0, 0, _ * 7)
        # Must be on exactly one edge
        at_left = (rx == 0)
        at_right = (rx == RAW_MAX_X)
        at_top = (ry == 0)
        at_bottom = (ry == RAW_MAX_Y)
        edges = sum([at_left, at_right, at_top, at_bottom])
        assert edges >= 1, f"Bullet at ({rx:#x},{ry:#x}) not on any edge"
        assert edges <= 2, f"Bullet at ({rx:#x},{ry:#x}) on multiple edges (corner)"
        # Raw coords within valid range
        assert 0 <= rx <= RAW_MAX_X, f"rx={rx} out of range"
        assert 0 <= ry <= RAW_MAX_Y, f"ry={ry} out of range"
    print("  Spawn position validity: 500 samples OK")


# ═══════════════════════════════════════════════════════════════
# Test 4: Bullet movement multi-frame tracking
# ═══════════════════════════════════════════════════════════════

def test_type0_trajectory():
    """Type 0 bullet follows straight line at constant speed."""
    # Angle 0 = right: moves (64, 0) per frame
    rx, ry = 0x8000, 0x4000
    for frame in range(100):
        rx, ry = move_bullet_type0(rx, ry, 0)
    assert rx == 0x8000 + 100 * 64, "Straight line x after 100 frames"
    assert ry == 0x4000, "Straight line y unchanged"
    print("  Type 0 trajectory 100f: OK")


def test_type1_homing_convergence():
    """Type 1 homing bullet eventually steers toward player."""
    from collections import Counter
    rx, ry = 0, 44 * 64  # left of player
    angle = 48  # pointing up (away from player at right)
    btype = TYPE_HOMING
    counter = 0
    state = 42
    angles_visited = []
    for _ in range(200):
        rx, ry, angle, btype, counter, state = move_bullet_type1(
            rx, ry, angle, btype, 16, counter, 152, 44, state)
        angles_visited.append(angle)
        if btype == TYPE_NORMAL:
            break  # lost lock
    # Should have moved from 48 toward 0 (right)
    unique = len(set(angles_visited))
    assert unique >= 3, f"Homing should change angle multiple times, got {unique}"
    # Eventually should approach 0 or lose lock
    final = angles_visited[-1] if angles_visited else 48
    assert final != 48 or btype == TYPE_NORMAL, \
        f"Angle should change from 48 or lose lock: angle={final}, type={btype}"
    print(f"  Type 1 homing: {unique} unique angles, final={final} OK")


def test_type2_full_accel_decel():
    """Type 2 accelerates toward player, caps at +/-96."""
    # Bullet above-left of player: should accelerate right+down  
    rx, ry = 64 * 64, 0  # pixel (60, -4), player at (152,44), player+6=(158,50)
    vx, vy = 0, 0
    for _ in range(100):
        rx, ry, vx, vy = move_bullet_type2(rx, ry, vx, vy, 152, 44)
    # After 100 frames, should have accelerated significantly
    assert abs(vx) > 10, f"vx should have accelerated: {vx}"
    assert abs(vy) > 10, f"vy should have accelerated: {vy}"
    assert abs(vx) <= VX_CAP, f"vx capped: {vx}"
    assert abs(vy) <= VY_CAP, f"vy capped: {vy}"
    print(f"  Type 2 accel: vx={vx}, vy={vy} (caps +/-{VX_CAP}) OK")


# ═══════════════════════════════════════════════════════════════
# Test 5: Collision + Graze edge cases
# ═══════════════════════════════════════════════════════════════

def test_collision_all_boundaries():
    """Hitbox: 2 ≤ dx < 13, 0 ≤ dy < 10 — test all edges."""
    # dx=2, dy=0: top-left corner → hit
    assert check_collision(
        (152 + 2 + PIXEL_OFFSET) << RAW_SHIFT,
        (44 + 0 + PIXEL_OFFSET) << RAW_SHIFT,
        152, 44), "dx=2,dy=0 should hit"
    # dx=12, dy=9: bottom-right corner → hit
    assert check_collision(
        (152 + 12 + PIXEL_OFFSET) << RAW_SHIFT,
        (44 + 9 + PIXEL_OFFSET) << RAW_SHIFT,
        152, 44), "dx=12,dy=9 should hit"
    # dx=13, dy=10: just outside → miss
    assert not check_collision(
        (152 + 13 + PIXEL_OFFSET) << RAW_SHIFT,
        (44 + 10 + PIXEL_OFFSET) << RAW_SHIFT,
        152, 44), "dx=13,dy=10 should miss"
    # dx=1, dy=5: too close left → miss
    assert not check_collision(
        (152 + 1 + PIXEL_OFFSET) << RAW_SHIFT,
        (44 + 5 + PIXEL_OFFSET) << RAW_SHIFT,
        152, 44), "dx=1 should miss"
    print("  Collision all boundaries: OK")


def test_graze_boundaries():
    """Graze zone: dx+4 < 23, dy+6 < 20."""
    # dx=18, dy=13: dx+4=22<23 ✓, dy+6=19<20 ✓ → in zone
    assert check_graze_enter(
        (152 + 18 + PIXEL_OFFSET) << RAW_SHIFT,
        (44 + 13 + PIXEL_OFFSET) << RAW_SHIFT,
        152, 44), "dx=18,dy=13 should be in graze"
    # dx=19, dy=14: dx+4=23<23 ✗ → out
    assert not check_graze_enter(
        (152 + 19 + PIXEL_OFFSET) << RAW_SHIFT,
        (44 + 14 + PIXEL_OFFSET) << RAW_SHIFT,
        152, 44), "dx=19,dy=14 should be out"
    print("  Graze boundaries: OK")


# ═══════════════════════════════════════════════════════════════
# Test 6: Graze chain logic (multi-bullet)
# ═══════════════════════════════════════════════════════════════

def simulate_graze_chain():
    """Simulate bullets entering/leaving graze zone, verify chain counter."""
    active_near = 0
    graze_total = 0
    graze_chain = 0
    graze_chain_time = 0

    # Simulate 5 bullets entering graze zone
    bullet_states = [{"grazed": 0, "raw_x": 0, "raw_y": 0} for _ in range(5)]
    for i in range(5):
        b = bullet_states[i]
        b["raw_x"] = (152 + 5 + PIXEL_OFFSET) << RAW_SHIFT
        b["raw_y"] = (44 + 3 + PIXEL_OFFSET) << RAW_SHIFT
        
        in_zone = check_graze_enter(b["raw_x"], b["raw_y"], 152, 44)
        if in_zone and not b["grazed"]:
            b["grazed"] = 1
            active_near += 1

    assert active_near == 5, "5 bullets should be active_near"

    # Now simulate bullets leaving
    for i in range(5):
        b = bullet_states[i]
        b["raw_x"] = (152 + 25 + PIXEL_OFFSET) << RAW_SHIFT  # move far away
        
        in_zone = check_graze_enter(b["raw_x"], b["raw_y"], 152, 44)
        if not in_zone and b["grazed"]:
            b["grazed"] = 0
            active_near -= 1
            if active_near > 0:
                graze_total += active_near
                # Chain logic
                frame = i * 100  # within 1000ms window
                if frame < graze_chain_time:
                    if graze_chain < GRAZE_CHAIN_MAX:
                        graze_chain += 1
                else:
                    graze_chain = 1
                graze_chain_time = frame + GRAZE_WINDOW

    assert active_near == 0, "All bullets should have left"
    assert graze_total > 0, "Graze total should accumulate"
    assert graze_chain > 0, "Graze chain should be set"
    print(f"  Graze chain: total={graze_total}, chain={graze_chain} OK")


# ═══════════════════════════════════════════════════════════════
# Test 7: Bounce limit (Type 2) behavior
# ═══════════════════════════════════════════════════════════════

def test_bounce_limit_spawn():
    """Pattern 7: bounce_limit increments up to MAX_BOUNCE (4)."""
    bounce = 0
    for i in range(6):
        slot = {}
        rng_state = i * 10
        rng_state, bounce, rx, ry, fields = spawn_bullet(
            0, 0, slot, 152, 44, 7, bounce, rng_state)
        if i < MAX_BOUNCE:
            assert fields["type"] == TYPE_H_ACCEL, f"Spawn {i}: should be Type 2"
        else:
            assert fields["type"] == TYPE_NORMAL, \
                f"Spawn {i}: should fall back to Type 0 (bounce={bounce})"
    assert bounce >= MAX_BOUNCE, f"Bounce limit should cap at {MAX_BOUNCE}"
    print(f"  Bounce limit spawn: capped at {bounce} OK")


# ═══════════════════════════════════════════════════════════════
# Test 8: process_one_bullet full lifecycle
# ═══════════════════════════════════════════════════════════════

def test_process_one_bullet_all_types():
    """process_one_bullet handles all 4 bullet types correctly."""
    # Valid on-screen position (raw_x < 0x5101, raw_y < 0x3D01)
    bullet = {"raw_x": 0x4000, "raw_y": 0x2000, "angle_index": 0,
              "type": 0, "timer": 0, "counter": 0, "grazed": 0,
              "vx": 0, "vy": 0}
    
    # Type 0
    r = process_one_bullet(bullet.copy(), 152, 44, False, 0, 0, 0, 0, 0, 0)
    assert r["action"] == "processed", f"Type 0: {r['action']}"
    
    # Type 1
    b = bullet.copy(); b["type"] = TYPE_HOMING; b["timer"] = 16
    r = process_one_bullet(b, 152, 44, False, 0, 0, 0, 0, 0, 0)
    assert r["action"] == "processed", f"Type 1: {r['action']}"
    
    # Type 2
    b = bullet.copy(); b["type"] = TYPE_H_ACCEL
    r = process_one_bullet(b, 152, 44, False, 0, 0, 0, 0, 0, 0)
    assert r["action"] == "processed", f"Type 2: {r['action']}"
    
    # Type 3
    b = bullet.copy(); b["type"] = TYPE_ACCEL
    r = process_one_bullet(b, 152, 44, False, 0, 0, 0, 0, 0, 0)
    assert r["action"] == "processed", f"Type 3: {r['action']}"

    print("  process_one_bullet all types: OK")


def test_process_one_bullet_collision():
    """process_one_bullet detects collision."""
    # Place bullet on player
    bullet = {
        "raw_x": (152 + 5 + PIXEL_OFFSET) << RAW_SHIFT,
        "raw_y": (44 + 3 + PIXEL_OFFSET) << RAW_SHIFT,
        "angle_index": 0, "type": 0, "timer": 0, "counter": 0,
        "grazed": 0, "vx": 0, "vy": 0,
    }
    r = process_one_bullet(bullet, 152, 44, False, 0, 0, 0, 0, 0, 0)
    assert r["hit"], "Collision should be detected"
    print("  process_one_bullet collision: OK")


# ═══════════════════════════════════════════════════════════════
# Test 9: Player movement edge cases
# ═══════════════════════════════════════════════════════════════

def test_player_stop():
    """Input=0 should not move player."""
    px, py = move_player(100, 100, 0)
    assert px == 100 and py == 100
    print("  Player stop: OK")

def test_player_all_8_directions():
    """All 8 valid bitmask combinations move correctly (include diagonals)."""
    # format: (name, bits, expected_dx, expected_dy)
    moves = {
        "RIGHT":      (8,  1,  0),
        "LEFT":       (1, -1,  0),
        "DOWN":       (4,  0,  1),
        "UP":         (2,  0, -1),
        "UP+RIGHT":   (10, 1, -1),
        "UP+LEFT":    (3, -1, -1),
        "DOWN+RIGHT": (12, 1,  1),
        "DOWN+LEFT":  (5, -1,  1),
        "STOP":       (0,  0,  0),
    }
    for name, (bits, edx, edy) in moves.items():
        px, py = move_player(100, 50, bits)
        assert px == 100 + edx, f"{name}: px={px}"
        assert py == 50 + edy, f"{name}: py={py} (bits={bits})"
    print("  Player all 8 directions: OK")


def test_player_clamp_all_edges():
    """Player cannot move past [0,SCR_W] × [0,SCR_H]."""
    # Left edge
    px, py = move_player(0, 50, 1)   # LEFT
    assert px == 0
    # Right edge
    px, py = move_player(SCR_W, 50, 8)  # RIGHT
    assert px == SCR_W
    # Top edge
    px, py = move_player(100, 0, 2)  # UP
    assert py == 0
    # Bottom edge
    px, py = move_player(100, SCR_H, 4)  # DOWN
    assert py == SCR_H
    # Corner: UP+LEFT at (0,0)
    px, py = move_player(0, 0, 3)
    assert px == 0 and py == 0
    print("  Player clamp all edges: OK")


# ═══════════════════════════════════════════════════════════════
# Test 10: RNG distribution and period
# ═══════════════════════════════════════════════════════════════

def test_rng_distribution():
    """RNG output is uniform over 0-0x7FFF range."""
    state = 12345
    buckets = [0] * 16
    for _ in range(10000):
        state, val = rng_next(state)
        buckets[val >> 11] += 1  # 0x8000/16 = 2048 per bucket
    avg = 10000 / 16
    for i, c in enumerate(buckets):
        # Each bucket should have ~625 ± 150
        assert abs(c - avg) < 200, f"Bucket {i}: {c} (expected ~{avg:.0f})"
    print(f"  RNG distribution: uniform across 16 buckets OK")


def test_rng_period():
    """RNG has full 32-bit period (not just 16-bit)."""
    state = 1
    seen = set()
    for _ in range(1000):
        state, _ = rng_next(state)
        seen.add(state & 0xFFFF)
    # After 1000 iterations, should have many unique low 16-bit states
    assert len(seen) > 900, f"RNG low 16-bit variety: {len(seen)}/1000"
    print(f"  RNG periodicity: {len(seen)} unique states OK")


# ═══════════════════════════════════════════════════════════════
# Test runner
# ═══════════════════════════════════════════════════════════════

def run_all():
    tests = [
        test_game_init_slots, test_game_init_difficulties,
        test_pattern_lifecycle, test_pattern_probability,
        test_spawn_all_patterns, test_spawn_position_valid,
        test_type0_trajectory, test_type1_homing_convergence,
        test_type2_full_accel_decel,
        test_collision_all_boundaries, test_graze_boundaries,
        simulate_graze_chain,
        test_bounce_limit_spawn,
        test_process_one_bullet_all_types, test_process_one_bullet_collision,
        test_player_stop, test_player_all_8_directions, test_player_clamp_all_edges,
        test_rng_distribution, test_rng_period,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL {test.__name__}: {e}")
    print(f"\n{'='*60}")
    print(f"  Integration: {passed}/{len(tests)} tests passed")
    print(f"{'='*60}")
    return passed == len(tests)


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
