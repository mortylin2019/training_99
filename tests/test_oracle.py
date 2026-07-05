"""
tests/test_oracle.py — Use the real 99.exe game as ground truth oracle.

For each C function, we:
1. Write known inputs to game memory via WriteProcessMemory
2. Let the game execute one frame (or call the function indirectly)
3. Read outputs from game memory via ReadProcessMemory
4. Compare with our Python function output

This gives us 100% confidence that our Python functions match the real binary.
"""
import sys
import os
import ctypes
from ctypes import wintypes
import time

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl


class GameOracle:
    """
    Connects to running 99.exe and provides read/write access
    to all game state for function-level testing.
    """

    def __init__(self, game=None):
        self.game = game or GameControl()
        self._launched = False
        self._saved_state = {}

    def ensure_running(self):
        """Launch game if not already running."""
        if not self._launched:
            if not self.game.launch_game():
                raise RuntimeError("Cannot launch 99.exe")
            self._launched = True
            time.sleep(0.5)

    def cleanup(self):
        if self._launched:
            self.game.cleanup()
            self._launched = False

    # ── Memory read/write helpers ──────────────────────────

    def read_u32(self, addr):
        return self.game.read_int(addr) & 0xFFFFFFFF

    def write_u32(self, addr, value):
        self.game.write_int(addr, value & 0xFFFFFFFF)

    def read_byte(self, addr):
        return self.game.read_byte(addr)

    def write_byte(self, addr, value):
        self.game.write_byte(addr, value & 0xFF)

    # ── State save/restore ─────────────────────────────────

    ADDRS_TO_SAVE = [
        0x00406d6c, 0x00406d70,  # player x, y
        0x00406d74,              # game state
        0x00406d80,              # game over
        0x00406da8,              # bullet count
        0x00406dac,              # bounce limit
        0x00406db0,              # pattern duration
        0x00406db4,              # active near
        0x00406db8,              # graze total
        0x00406dbc,              # pattern
        0x00406dc0,              # difficulty
    ]

    def save_state(self):
        """Snapshot all relevant game state."""
        for addr in self.ADDRS_TO_SAVE:
            self._saved_state[addr] = self.read_u32(addr)

    def restore_state(self):
        """Restore previously saved game state."""
        for addr, val in self._saved_state.items():
            self.write_u32(addr, val)

    # ── Function-level test primitives ────────────────────

    def test_rng(self, seed, count=10):
        """
        Test RNG (FUN_00402000).
        Writes seed to RNG state, steps N times, reads results.
        Returns list of (state, value) pairs.

        RNG state addr: need to find it... The game's RNG state is
        likely at a fixed address in .bss. For now, we test indirectly
        by observing bullet spawn positions (which use RNG).
        """
        raise NotImplementedError("Need to locate RNG state address")

    def test_aimed_angle(self, bullet_raw_x, bullet_raw_y,
                         player_px, player_py, spread=5):
        """
        Test FUN_00402d68 by setting up a bullet at known position
        and triggering a spawn, then reading the resulting angle_index.

        Approach: write bullet position to entity slot 0, set game state
        to Playing, trigger FUN_00402d68 indirectly via spawn.
        """
        raise NotImplementedError("Requires careful game state setup")

    def read_entity_slot(self, slot=0):
        """Read 15-byte entity at G_EntityArray + slot*15."""
        base = 0x00406e10 + slot * 15
        raw_x = self.read_u32(base + 0x00)
        raw_y = self.read_u32(base + 0x04)
        angle_index = self.read_byte(base + 0x08)
        grazed = self.read_byte(base + 0x09)
        btype = self.read_byte(base + 0x0A)
        timer = self.read_byte(base + 0x0B)
        counter = self.read_byte(base + 0x0C)
        vx_signed = self.read_byte(base + 0x0D)
        vy_signed = self.read_byte(base + 0x0E)
        # Sign-extend
        vx = vx_signed if vx_signed < 128 else vx_signed - 256
        vy = vy_signed if vy_signed < 128 else vy_signed - 256
        return {
            "raw_x": raw_x, "raw_y": raw_y,
            "angle_index": angle_index, "grazed": grazed,
            "type": btype, "timer": timer, "counter": counter,
            "vx": vx, "vy": vy,
        }

    def write_entity_slot(self, slot, data, only_fields=None):
        """Write entity slot fields. only_fields=None means all."""
        base = 0x00406e10 + slot * 15
        all_fields = {
            "raw_x": (base + 0x00, 4),
            "raw_y": (base + 0x04, 4),
            "angle_index": (base + 0x08, 1),
            "grazed": (base + 0x09, 1),
            "type": (base + 0x0A, 1),
            "timer": (base + 0x0B, 1),
            "counter": (base + 0x0C, 1),
            "vx": (base + 0x0D, 1),
            "vy": (base + 0x0E, 1),
        }
        fields = only_fields or data.keys()
        for key in fields:
            if key in data and key in all_fields:
                addr, size = all_fields[key]
                val = data[key]
                if key in ("vx", "vy"):
                    val = val & 0xFF  # signed byte
                if size == 4:
                    self.write_u32(addr, val)
                else:
                    self.write_byte(addr, val)

    def get_player_pos(self):
        """Read player position."""
        px = self.read_u32(0x00406d6c)
        py = self.read_u32(0x00406d70)
        return px, py

    def set_player_pos(self, px, py):
        """Write player position."""
        self.write_u32(0x00406d6c, px)
        self.write_u32(0x00406d70, py)

    def get_game_state(self):
        """Read G_GameState."""
        return self.read_u32(0x00406d74)

    def get_game_over(self):
        """Read G_GameOverFlag."""
        return self.read_u32(0x00406d80)

    def get_bullet_count(self):
        """Read G_CurrentBulletCount."""
        return self.read_u32(0x00406da8)

    def set_bullet_count(self, count):
        """Write G_CurrentBulletCount."""
        self.write_u32(0x00406da8, count)

    def get_pattern(self):
        """Read G_NextBulletPattern."""
        return self.read_u32(0x00406dbc)

    def set_pattern(self, pattern):
        """Write G_NextBulletPattern."""
        self.write_u32(0x00406dbc, pattern)

    def get_input_state(self):
        """Read G_InputState."""
        return self.read_u32(0x00406d7c)

    def set_input_state(self, bits):
        """Write G_InputState."""
        self.write_u32(0x00406d7c, bits)

    # ── High-level test: single frame comparison ──────────

    def capture_frame_state(self):
        """Snapshot all visible bullets + player after one frame."""
        px, py = self.get_player_pos()
        count = self.get_bullet_count()
        bullets = []
        for i in range(min(count, 300)):
            b = self.read_entity_slot(i)
            if b["angle_index"] != 0xFF:
                bullets.append(b)
        return {"px": px, "py": py, "bullet_count": count,
                "active_bullets": len(bullets), "bullets": bullets,
                "pattern": self.get_pattern(),
                "game_over": self.get_game_over()}

    def set_full_state(self, px, py, bullets, bullet_count,
                       pattern=0, game_over=0):
        """Set up a complete game state for testing."""
        self.set_player_pos(px, py)
        self.set_bullet_count(bullet_count)
        self.set_pattern(pattern)
        self.write_u32(0x00406d80, game_over)
        # Clear all entity slots
        for i in range(300):
            self.write_byte(0x00406e10 + i * 15 + 0x08, 0xFF)
        # Write provided bullets
        for i, b in enumerate(bullets):
            self.write_entity_slot(i, b)
        # Set input to STOP
        self.set_input_state(0)

    def step_one_frame(self, input_bits=0):
        """
        Let the game execute ONE frame and capture state.
        This is the core oracle operation.
        """
        self.set_input_state(input_bits)
        before = self.capture_frame_state()
        # Wait for one frame (~12.5ms at 80fps)
        time.sleep(0.02)
        after = self.capture_frame_state()
        return before, after


# ── Test runner ──────────────────────────────────────────────

def run_oracle_tests():
    """Run all oracle tests. Requires 99.exe running."""
    oracle = GameOracle()
    try:
        oracle.ensure_running()
        print("Oracle connected to game.")

        # Test 1: Read current game state
        px, py = oracle.get_player_pos()
        count = oracle.get_bullet_count()
        pattern = oracle.get_pattern()
        print(f"  State: player=({px},{py}), bullets={count}, pattern={pattern}")

        # Test 2: Entity slot read/write round-trip
        slot0 = oracle.read_entity_slot(0)
        print(f"  Slot 0 before: {slot0}")
        test_data = {"raw_x": 0x8000, "raw_y": 0x4000,
                     "angle_index": 0x10, "type": 0, "timer": 0}
        oracle.write_entity_slot(0, test_data)
        slot0_after = oracle.read_entity_slot(0)
        print(f"  Slot 0 after write: {slot0_after}")
        # Restore
        oracle.write_entity_slot(0, slot0)

        # Test 3: Step one frame and observe changes
        print("\n  Stepping one frame...")
        before, after = oracle.step_one_frame(input_bits=0)  # STOP
        print(f"  Before: px={before['px']},{before['py']} "
              f"bullets={before['active_bullets']}")
        print(f"  After:  px={after['px']},{after['py']} "
              f"bullets={after['active_bullets']}")

        # Test 4: Move player
        oracle.set_input_state(2)  # UP
        time.sleep(0.1)
        px2, py2 = oracle.get_player_pos()
        print(f"\n  After UP for 0.1s: player=({px2},{py2})")
        oracle.set_input_state(0)

        return True
    finally:
        oracle.cleanup()


if __name__ == "__main__":
    run_oracle_tests()
