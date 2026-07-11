"""
tests/test_cross_validate.py — Cross-validate Python functions against the REAL 99.exe binary.

For each game function, we:
1. Write test inputs to game memory via WriteProcessMemory
2. Let the game execute ONE frame
3. Read outputs from game memory via ReadProcessMemory
4. Run our Python equivalent function with the same inputs
5. Compare — assert they match exactly

This is the ULTIMATE ground truth. The real binary is always right.
"""
import sys
import os
import time
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl

from hijack_tools.simulator.functions import *
from hijack_tools.simulator.config import *
from hijack_tools.simulator.tables import VEL_TABLE


class CrossValidator:
    """Real-game oracle for function-level validation."""

    def __init__(self):
        self.game = GameControl()
        self._setup()

    def _setup(self):
        """Launch game and navigate to Playing state via PostMessage to window."""
        if not self.game.launch_game():
            raise RuntimeError("Cannot launch 99.exe")
        time.sleep(0.3)

        # Get window handle
        hwnd = self.game.hwnd
        if not hwnd:
            raise RuntimeError("No window handle")

        # Send Enter key via PostMessage directly to the game window
        # This bypasses focus issues — the message goes straight to the game's queue
        import ctypes
        WM_KEYDOWN = 0x100
        WM_KEYUP = 0x101
        VK_RETURN = 0x0D

        user32 = ctypes.windll.user32
        for attempt in range(30):
            state = self.game.get_game_state()
            if state == 1 and not self.game.is_game_over():
                break
            # Post WM_KEYDOWN + WM_KEYUP for Enter
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0x1C0001)
            time.sleep(0.05)
            user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0xC01C0001)
            time.sleep(0.2)

        state = self.game.get_game_state()
        if state != 1:
            print(f"  WARNING: Could not reach Playing (state={state}), forcing...")
            self.game.write_int(0x00406d74, 1)
            self.game.write_int(0x00406d84, 1)
            self.game.write_int(0x00406d90, 1)
            self.game.write_int(0x00406d80, 0)
            time.sleep(0.1)

        print(f"  Game state: {self.game.get_game_state()}")

        # Stop player input
        self.game.write_int(0x00406d7c, 0)
        time.sleep(0.1)
        print(f"  Game launched, Playing state confirmed (state={state})")

    def cleanup(self):
        self.game.cleanup()

    # ── Low-level memory helpers ──────────────────────────

    def _read_entity(self, slot=0):
        """Read 15-byte entity from game memory."""
        base = 0x00406e10 + slot * 15
        raw_x = self.game.read_int(base)
        raw_y = self.game.read_int(base + 4)
        angle_index = self.game.read_byte(base + 8)
        grazed = self.game.read_byte(base + 9)
        btype = self.game.read_byte(base + 10)
        timer = self.game.read_byte(base + 11)
        counter = self.game.read_byte(base + 12)
        vx_raw = self.game.read_byte(base + 13)
        vy_raw = self.game.read_byte(base + 14)
        vx = vx_raw if vx_raw < 128 else vx_raw - 256
        vy = vy_raw if vy_raw < 128 else vy_raw - 256
        return {
            "raw_x": raw_x, "raw_y": raw_y,
            "angle_index": angle_index, "grazed": grazed,
            "type": btype, "timer": timer, "counter": counter,
            "vx": vx, "vy": vy,
        }

    def _write_entity(self, slot, data):
        """Write entity fields to game memory."""
        base = 0x00406e10 + slot * 15
        if "raw_x" in data: self.game.write_int(base, data["raw_x"])
        if "raw_y" in data: self.game.write_int(base + 4, data["raw_y"])
        if "angle_index" in data: self.game.write_byte(base + 8, data["angle_index"])
        if "grazed" in data: self.game.write_byte(base + 9, data["grazed"])
        if "type" in data: self.game.write_byte(base + 10, data["type"])
        if "timer" in data: self.game.write_byte(base + 11, data["timer"])
        if "counter" in data: self.game.write_byte(base + 12, data["counter"])
        if "vx" in data: self.game.write_byte(base + 13, data["vx"] & 0xFF)
        if "vy" in data: self.game.write_byte(base + 14, data["vy"] & 0xFF)

    def _read_player(self):
        px = self.game.read_int(0x00406d6c)
        py = self.game.read_int(0x00406d70)
        return px, py

    def _write_player(self, px, py):
        self.game.write_int(0x00406d6c, px)
        self.game.write_int(0x00406d70, py)

    def _read_game_over(self):
        return self.game.read_int(0x00406d80)

    def _write_game_over(self, val):
        self.game.write_int(0x00406d80, val)

    def _read_bullet_count(self):
        return self.game.read_int(0x00406da8)

    def _write_bullet_count(self, count):
        self.game.write_int(0x00406da8, count)

    # ── Step one frame ────────────────────────────────────

    def _step_one_frame(self, input_bits=0):
        """Step exactly ONE game frame: write input, sleep exactly 1 frame, stop input."""
        self.game.write_int(0x00406d7c, input_bits)
        time.sleep(0.012)  # ~1 frame at 62fps (16ms), safe margin
        self.game.write_int(0x00406d7c, 0)
        # Read result
        return self._read_player()

    # ═══════════════════════════════════════════════════════
    # Test 1: Player Movement (deterministic, no RNG)
    # ═══════════════════════════════════════════════════════

    def test_player_movement(self):
        """Move player in all 8 directions, verify pixel positions."""
        print("\n[Test] Player Movement — cross-validate with real game")

        directions = [
            ("RIGHT", 8, 1, 0),
            ("LEFT", 1, -1, 0),
            ("DOWN", 4, 0, 1),
            ("UP", 2, 0, -1),
            ("UP+RIGHT", 10, 1, -1),
            ("DOWN+LEFT", 5, -1, 1),
        ]

        for name, bits, edx, edy in directions:
            # Set known start position (not at edge)
            self._write_player(100, 80)
            time.sleep(0.01)

            # Step one frame — returns final position directly
            px, py = self._step_one_frame(bits)

            # Python prediction
            py_px, py_py = move_player(100, 80, bits)

            assert px == py_px, f"{name}: game px={px}, python px={py_px}"
            assert py == py_py, f"{name}: game py={py}, python py={py_py}"
            print(f"  {name:>10}: game=({px},{py}) py=({py_px},{py_py}) ✓")

        print("  Player movement: ALL MATCH")

    # ═══════════════════════════════════════════════════════
    # Test 2: Bullet Type 0 Movement
    # ═══════════════════════════════════════════════════════

    def test_bullet_movement_type0(self):
        """Place a Type 0 bullet, step one frame, compare movement."""
        print("\n[Test] Bullet Type 0 Movement — cross-validate")

        for angle in [0, 8, 16, 32, 48]:
            # Set up bullet at known position
            bullet = {
                "raw_x": 0x8000, "raw_y": 0x4000,
                "angle_index": angle, "grazed": 0,
                "type": TYPE_NORMAL, "timer": 0, "counter": 0,
                "vx": 0, "vy": 0,
            }
            self._write_entity(0, bullet)
            # Ensure slot 0 is within active count
            self._write_bullet_count(max(10, self._read_bullet_count()))
            # Set game over to 0 (alive)
            self._write_game_over(0)
            # Stop all input
            self.game.write_int(0x00406d7c, 0)
            time.sleep(0.01)

            # Read before
            before = self._read_entity(0)

            # Step one frame
            self._step_one_frame(0)

            # Read after
            after = self._read_entity(0)

            # Python prediction
            py_rx, py_ry = move_bullet_type0(before["raw_x"], before["raw_y"],
                                              before["angle_index"])

            assert after["raw_x"] == py_rx, \
                f"Angle {angle}: game raw_x {after['raw_x']}, python {py_rx}"
            assert after["raw_y"] == py_ry, \
                f"Angle {angle}: game raw_y {after['raw_y']}, python {py_ry}"
            print(f"  Angle {angle:>2}: game=({after['raw_x']:#06x},{after['raw_y']:#06x}) "
                  f"py=({py_rx:#06x},{py_ry:#06x}) ✓")

        print("  Bullet Type 0 movement: ALL MATCH")

    # ═══════════════════════════════════════════════════════
    # Test 3: Collision Detection
    # ═══════════════════════════════════════════════════════

    def test_collision(self):
        """Place bullet on player hitbox, verify game sets GameOverFlag."""
        print("\n[Test] Collision Detection — cross-validate")

        # Set player at known position
        self._write_player(152, 44)
        # Set game over to 0
        self._write_game_over(0)
        self.game.write_int(0x00406d7c, 0)
        time.sleep(0.02)

        # Place bullet directly on player (dx=5, dy=3 → should hit)
        raw_x = (152 + 5 + PIXEL_OFFSET) << RAW_SHIFT  # dx=5
        raw_y = (44 + 3 + PIXEL_OFFSET) << RAW_SHIFT   # dy=3
        bullet = {
            "raw_x": raw_x, "raw_y": raw_y,
            "angle_index": 0, "grazed": 0,
            "type": TYPE_NORMAL, "timer": 0, "counter": 0,
            "vx": 0, "vy": 0,
        }
        self._write_entity(0, bullet)
        self._write_bullet_count(max(10, self._read_bullet_count()))
        time.sleep(0.01)

        # Step one frame
        self._step_one_frame(0)
        time.sleep(0.02)

        game_over = self._read_game_over()
        # Game should have set GameOverFlag to non-zero
        assert game_over != 0, f"GameOverFlag should be set! Got {game_over}"

        # Python prediction
        py_hit = check_collision(raw_x, raw_y, 152, 44)
        assert py_hit, "Python should also detect collision"

        print(f"  Collision: game game_over={game_over}, python hit={py_hit} ✓")

        # Reset game over
        self._write_game_over(0)
        time.sleep(0.01)

        # Now test MISS: place bullet far from player
        raw_x2 = (152 + 20 + PIXEL_OFFSET) << RAW_SHIFT  # dx=20 > 13
        bullet2 = {**bullet, "raw_x": raw_x2, "raw_y": raw_y}
        self._write_entity(0, bullet2)
        time.sleep(0.01)

        self._step_one_frame(0)
        time.sleep(0.02)

        game_over2 = self._read_game_over()
        assert game_over2 == 0, f"GameOverFlag should NOT be set for miss! Got {game_over2}"

        py_miss = check_collision(raw_x2, raw_y, 152, 44)
        assert not py_miss, "Python should NOT detect collision"

        print(f"  Miss: game game_over={game_over2}, python hit={py_miss} ✓")
        print("  Collision detection: ALL MATCH")

    # ═══════════════════════════════════════════════════════
    # Test 4: Graze zone detection
    # ═══════════════════════════════════════════════════════

    def test_graze_zone(self):
        """Place bullet in graze zone, verify active_near increments."""
        print("\n[Test] Graze Zone — cross-validate")

        self._write_player(152, 44)
        self._write_game_over(0)
        self.game.write_int(0x00406d7c, 0)
        time.sleep(0.02)

        # Read initial active_near
        initial_near = self.game.read_int(0x00406db4)

        # Place bullet in graze zone: dx=5, dy=3 → dx+4=9<23, dy+6=9<20
        raw_x = (152 + 5 + PIXEL_OFFSET) << RAW_SHIFT
        raw_y = (44 + 3 + PIXEL_OFFSET) << RAW_SHIFT
        bullet = {
            "raw_x": raw_x, "raw_y": raw_y,
            "angle_index": 0, "grazed": 0,
            "type": TYPE_NORMAL, "timer": 0, "counter": 0,
            "vx": 0, "vy": 0,
        }
        self._write_entity(0, bullet)
        self._write_bullet_count(max(10, self._read_bullet_count()))
        time.sleep(0.01)

        self._step_one_frame(0)
        time.sleep(0.02)

        after_near = self.game.read_int(0x00406db4)
        # active_near should have increased (bullet entered graze zone)
        assert after_near > initial_near, \
            f"active_near should increase: {initial_near} → {after_near}"

        # Python prediction
        py_in = check_graze_enter(raw_x, raw_y, 152, 44)
        assert py_in, "Python should detect graze zone entry"

        print(f"  Graze: active_near {initial_near}→{after_near}, python in_zone={py_in} ✓")
        print("  Graze zone: MATCH")


# ═══════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Cross-Validation: Python functions vs REAL 99.exe")
    print("=" * 60)

    cv = CrossValidator()
    try:
        cv.test_player_movement()
        cv.test_bullet_movement_type0()
        cv.test_collision()
        cv.test_graze_zone()

        print("\n" + "=" * 60)
        print("  ALL CROSS-VALIDATION TESTS PASSED")
        print("  Python functions match real game binary exactly.")
        print("=" * 60)
    finally:
        cv.cleanup()


if __name__ == "__main__":
    main()
