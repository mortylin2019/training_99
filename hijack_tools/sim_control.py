"""
sim_control.py — Simulator-backed GameControl-compatible interface.
Replaces real 99.exe process hijacking with the offline simulator,
while keeping the same runner UI/video/AI integration.

Usage (in runner.py): set game = SimControl(difficulty=1, seed=42) instead of GameControl()
"""
import time
from loguru import logger

try:
    from simulator.engine import GameSimulator
    from simulator.tables import VEL_TABLE, ACCEL_TABLE
    from simulator.config import FPS as SIM_FPS
except ImportError:
    from hijack_tools.simulator.engine import GameSimulator
    from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE
    from hijack_tools.simulator.config import FPS as SIM_FPS


class SimControl:
    """GameControl-compatible wrapper around GameSimulator."""

    STATE_PLAYING = 1
    STATE_TITLE = 0
    STATE_RESULT = 5
    STATE_RANKING = 6

    def __init__(self, difficulty=1, seed=0):
        self._sim = GameSimulator(difficulty=difficulty, seed=seed)
        self._state = self.STATE_TITLE
        self._dead = False
        self._playing = False
        self._run_started = False
        self._death_time = 0.0
        self._game_start = None
        self.hwnd = None
        self.process_handle = True  # truthy — keeps runner's background thread alive
        self.vel_table = VEL_TABLE
        self.accel_table = ACCEL_TABLE

    # ── GameControl-compatible interface ────────────────────────

    def launch_game(self):
        logger.info("SimControl: simulator ready (no .exe needed)")
        return True

    def close(self):
        pass

    @property
    def px(self):
        return self._sim.px

    @property
    def py(self):
        return self._sim.py

    def get_player_pos(self):
        return self._sim.px, self._sim.py

    def get_bullets(self):
        return self._sim.get_visible_bullets()

    def get_game_state(self):
        return self._state

    def is_playing(self):
        return self._playing and not self._dead

    def is_game_over(self):
        return self._dead

    def get_survival_ms(self):
        if self._playing and not self._dead:
            return int(self._sim.frame / SIM_FPS * 1000)
        return int(self._death_time * 1000) if self._death_time > 0 else 0

    def get_game_time(self):
        return self._sim.frame

    def get_score_multiplier(self):
        return 16

    def write_int(self, addr, value):
        """Write to simulated G_InputState (0x00406d7c only)."""
        if addr == 0x00406d7c:
            self._step(value)
        # Other addresses ignored (menu navigation handled via state machine)

    def press_enter(self):
        """Auto-advance through title/result/ranking screens."""
        if self._state == self.STATE_TITLE:
            # Title → start playing
            self._sim.reset()
            self._state = self.STATE_PLAYING
            self._playing = True
            self._dead = False
            self._game_start = time.perf_counter()
            self._run_started = True
        elif self._state == self.STATE_RESULT:
            self._state = self.STATE_RANKING
        elif self._state == self.STATE_RANKING:
            self._state = self.STATE_TITLE
            self._playing = False
            self._run_started = False

    def read_rng_state(self):
        return self._sim.rng.state

    def get_next_pattern(self):
        return self._sim.pattern

    def get_active_near(self):
        return self._sim.active_near

    def read_int(self, addr):
        """Read simulated memory address."""
        if addr == 0x00405c00:
            return self._sim.rng.state
        if addr == 0x00406dbc:
            return self._sim.pattern
        return 0

    def cleanup(self):
        pass

    def read_memory(self, addr, size):
        """Read simulated memory: supports VEL_TABLE at 0x00405d74 and ACCEL_TABLE at 0x00406074."""
        import struct
        if 0x00405d74 <= addr < 0x00405d74 + 64 * 12:
            byte_off = addr - 0x00405d74
            entry = byte_off // 12
            field = (byte_off % 12) // 4  # 0=vx, 1=vy, 2=tan_ratio
            vals = VEL_TABLE[entry % 64]
            if size == 8 and field == 0:
                return struct.pack('<ii', vals[0], vals[1])
            if size == 4:
                return struct.pack('<i', vals[field % 3])
        if 0x00406074 <= addr < 0x00406074 + 64 * 12:
            byte_off = addr - 0x00406074
            entry = byte_off // 12
            field = (byte_off % 12) // 4
            vals = ACCEL_TABLE[entry % 64]
            if size == 8 and field == 0:
                return struct.pack('<ii', vals[0], vals[1])
            if size == 4:
                return struct.pack('<i', vals[field % 3])
        return b'\x00' * size

    # ── Internal ────────────────────────────────────────────────

    def _step(self, bits):
        if not self._playing or self._dead:
            return
        alive, _ = self._sim.step(bits)
        time.sleep(1 / 62.5)  # match real game frame pacing
        if not alive:
            self._dead = True
            self._playing = False
            self._death_time = self._sim.frame / SIM_FPS
            self._state = self.STATE_RESULT
