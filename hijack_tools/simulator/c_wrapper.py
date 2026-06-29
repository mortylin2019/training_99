"""
simulator/c_wrapper.py — Python ctypes wrapper for sim_core.dll (C engine).

Same API as engine.GameSimulator — drop-in replacement for benchmarking.
"""
import ctypes
import os

_DLL_PATH = os.path.join(os.path.dirname(__file__), "sim_core.dll")
_lib = ctypes.CDLL(_DLL_PATH)

# ── Type setup ──────────────────────────────────────────────
_lib.sim_create.argtypes = [ctypes.c_int, ctypes.c_int]
_lib.sim_create.restype = ctypes.c_void_p

_lib.sim_destroy.argtypes = [ctypes.c_void_p]
_lib.sim_destroy.restype = None

_lib.sim_reset.argtypes = [ctypes.c_void_p]
_lib.sim_reset.restype = None

_lib.sim_step.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.sim_step.restype = ctypes.c_int

_lib.sim_get_player.argtypes = [ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int)]
_lib.sim_get_player.restype = None

_lib.sim_get_bullet_count.argtypes = [ctypes.c_void_p]
_lib.sim_get_bullet_count.restype = ctypes.c_int

_lib.sim_get_bullet.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int)]
_lib.sim_get_bullet.restype = None

_lib.sim_get_graze.argtypes = [ctypes.c_void_p]
_lib.sim_get_graze.restype = ctypes.c_int

_lib.sim_get_frame.argtypes = [ctypes.c_void_p]
_lib.sim_get_frame.restype = ctypes.c_int

_lib.sim_get_rng.argtypes = [ctypes.c_void_p]
_lib.sim_get_rng.restype = ctypes.c_uint

# ── State loading (real-game replay) ────────────────────────
_lib.sim_set_player.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_lib.sim_set_player.restype = None

_lib.sim_set_rng.argtypes = [ctypes.c_void_p, ctypes.c_uint]
_lib.sim_set_rng.restype = None

_lib.sim_set_pattern.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_lib.sim_set_pattern.restype = None

_lib.sim_set_next_spawn.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.sim_set_next_spawn.restype = None

_lib.sim_set_frame.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.sim_set_frame.restype = None

_lib.sim_load_bullets.argtypes = [ctypes.c_void_p, ctypes.c_int,
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
_lib.sim_load_bullets.restype = None

# ── Combined step + grid state (fast path for RL) ────────────
_lib.sim_step_with_grid.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                      ctypes.POINTER(ctypes.c_float)]
_lib.sim_step_with_grid.restype = ctypes.c_int

# ── C inference engine ──────────────────────────────────────
_lib.sim_load_weights.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int]
_lib.sim_load_weights.restype = None

_lib.sim_run_episode_c.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_float]
_lib.sim_run_episode_c.restype = ctypes.c_int

# ── Batch episode callback type ─────────────────────────────
AI_CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,  # return: input bits
    ctypes.c_int, ctypes.c_int,  # px, py
    ctypes.c_int,  # n (bullet count)
    ctypes.POINTER(ctypes.c_int),  # bx array
    ctypes.POINTER(ctypes.c_int),  # by array
    ctypes.POINTER(ctypes.c_int),  # types array
    ctypes.POINTER(ctypes.c_int),  # angles array
    ctypes.POINTER(ctypes.c_int),  # vx array
    ctypes.POINTER(ctypes.c_int),  # vy array
    ctypes.c_int,  # graze
    ctypes.c_int,  # frame
)

_lib.sim_run_episode.argtypes = [ctypes.c_void_p, ctypes.c_int, AI_CALLBACK]
_lib.sim_run_episode.restype = ctypes.c_int

# ── C beam search (CHECK_EVERY=1, DEPTH=160, WIDTH=12) ─────
_lib.sim_beam_search.argtypes = [ctypes.c_void_p]
_lib.sim_beam_search.restype = ctypes.c_int

_lib.sim_beam_search_raw.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int)]
_lib.sim_beam_search_raw.restype = ctypes.c_int


class Bullet:
    """Bullet data matching simulator/bullet.py Bullet interface."""
    __slots__ = ('x', 'y', 'type', 'angle_index', 'vx', 'vy')

    def __init__(self, x=0, y=0, type=0, angle_index=0, vx=0, vy=0):
        self.x = x
        self.y = y
        self.type = type
        self.angle_index = angle_index
        self.vx = vx
        self.vy = vy


class CSimulator:
    """C engine wrapper — same API as GameSimulator."""

    def __init__(self, difficulty=1, seed=0, spawn_interval_ms=None):
        self._ptr = _lib.sim_create(difficulty, seed)
        if not self._ptr:
            raise RuntimeError("Failed to create C simulator")
        self.difficulty = difficulty

    def __del__(self):
        if hasattr(self, '_ptr') and self._ptr:
            _lib.sim_destroy(self._ptr)

    def reset(self):
        _lib.sim_reset(self._ptr)

    def step(self, input_bits):
        """Returns (alive, visible_bullets)."""
        alive = bool(_lib.sim_step(self._ptr, input_bits))
        bullets = self.get_visible_bullets()
        return alive, bullets

    @property
    def px(self):
        x, y = ctypes.c_int(), ctypes.c_int()
        _lib.sim_get_player(self._ptr, ctypes.byref(x), ctypes.byref(y))
        return x.value

    @property
    def py(self):
        x, y = ctypes.c_int(), ctypes.c_int()
        _lib.sim_get_player(self._ptr, ctypes.byref(x), ctypes.byref(y))
        return y.value

    @property
    def active_near(self):
        return _lib.sim_get_graze(self._ptr)

    @property
    def frame(self):
        return _lib.sim_get_frame(self._ptr)

    @property
    def dead(self):
        # A bit hacky: step returns 0 when dead, we track via step return
        return False  # C engine doesn't expose dead directly; use step return

    def get_visible_bullets(self):
        """Return list of Bullet objects for active bullets."""
        result = []
        x, y, t, a, vx, vy = (ctypes.c_int() for _ in range(6))
        max_slots = _lib.sim_get_bullet_count(self._ptr) + 50
        for i in range(min(max_slots, 300)):
            _lib.sim_get_bullet(self._ptr, i, ctypes.byref(x), ctypes.byref(y),
                               ctypes.byref(t), ctypes.byref(a),
                               ctypes.byref(vx), ctypes.byref(vy))
            if a.value == 0xFF:
                continue
            result.append(Bullet(x=x.value, y=y.value, type=t.value,
                                 angle_index=a.value, vx=vx.value, vy=vy.value))
        return result

    def beam_search(self):
        """Run C beam search on current CSimulator state. Returns bitmask (0-12)."""
        return _lib.sim_beam_search(self._ptr)

    def set_player(self, px, py):
        """Set player position (for state replay)."""
        _lib.sim_set_player(self._ptr, px, py)

    def set_rng(self, rng):
        """Set RNG state (for state replay)."""
        _lib.sim_set_rng(self._ptr, rng)

    def set_pattern(self, pattern, next_pattern):
        """Set pattern state (for state replay)."""
        _lib.sim_set_pattern(self._ptr, pattern, next_pattern)

    def set_next_spawn(self, next_spawn):
        """Set next spawn frame (for state replay)."""
        _lib.sim_set_next_spawn(self._ptr, next_spawn)

    def set_frame(self, frame):
        """Set frame counter (for state replay)."""
        _lib.sim_set_frame(self._ptr, frame)

    def load_bullets(self, bullet_tuples):
        """Load bullets from list of (raw_x, raw_y, angle, type, timer, counter, vx, vy) tuples."""
        n = len(bullet_tuples)
        rx = (ctypes.c_int * n)(*[b[0] for b in bullet_tuples])
        ry = (ctypes.c_int * n)(*[b[1] for b in bullet_tuples])
        ai = (ctypes.c_int * n)(*[b[2] for b in bullet_tuples])
        ty = (ctypes.c_int * n)(*[b[3] for b in bullet_tuples])
        ti = (ctypes.c_int * n)(*[b[4] for b in bullet_tuples])
        ct = (ctypes.c_int * n)(*[b[5] for b in bullet_tuples])
        vx = (ctypes.c_int * n)(*[b[6] for b in bullet_tuples])
        vy = (ctypes.c_int * n)(*[b[7] for b in bullet_tuples])
        _lib.sim_load_bullets(self._ptr, n, rx, ry, ai, ty, ti, ct, vx, vy)

    def beam_search_raw(self, px, py, bullets):
        """Run C beam search from bullet arrays (no simulator sync).
        bullets: list of (x, y, angle_index) tuples.
        Returns bitmask (0-12)."""
        n = len(bullets)
        bx = (ctypes.c_int * n)(*[b[0] for b in bullets])
        by = (ctypes.c_int * n)(*[b[1] for b in bullets])
        ai = (ctypes.c_int * n)(*[b[2] for b in bullets])
        return _lib.sim_beam_search_raw(px, py, n, bx, by, ai)

    def step_with_grid(self, input_bits, grid_out):
        """
        One sim step + compute grid state in C (eliminates Python encode_state).
        grid_out: numpy (4, 24, 32) float32 array, filled in-place.
        Returns alive (bool).
        """
        alive = _lib.sim_step_with_grid(
            self._ptr, input_bits,
            grid_out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        return bool(alive)

    def run_episode(self, ai, max_frames=8000):
        """
        Run a full episode with the given AI, entirely in C loop.
        `ai` must have a decide(px, py, bullets, **kwargs) → bits method.
        Eliminates per-frame ctypes overhead (8000 calls → 1 call).
        Returns frames survived.
        """
        @AI_CALLBACK
        def _cb(px, py, n, bx_ptr, by_ptr, types_ptr, angles_ptr,
                vx_ptr, vy_ptr, graze, frame):
            bullets = []
            for i in range(n):
                bullets.append(Bullet(
                    x=bx_ptr[i], y=by_ptr[i], type=types_ptr[i],
                    angle_index=angles_ptr[i], vx=vx_ptr[i], vy=vy_ptr[i]))
            import inspect
            try:
                bits = ai.decide(px, py, bullets, graze=graze, frame=frame)
            except TypeError:
                bits = ai.decide(px, py, bullets)
            return bits

        return _lib.sim_run_episode(self._ptr, max_frames, _cb)


def load_weights_to_c(bin_path):
    """Load exported .bin weights into the C inference engine."""
    import numpy as np
    weights = np.fromfile(bin_path, dtype=np.float32)
    _lib.sim_load_weights(
        weights.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        len(weights))
    return len(weights)


def run_episode_c(c_sim, max_frames=8000, epsilon=0.0):
    """
    Run one episode with pure C inference (zero Python callbacks).
    Requires sim_load_weights() to have been called first.
    epsilon: exploration rate (0.0 = pure greedy, 1.0 = pure random)
    Returns frames survived.
    """
    return _lib.sim_run_episode_c(c_sim._ptr, max_frames, ctypes.c_float(epsilon))


# ── Standalone C beam search (no CSimulator instance needed) ─
def c_beam_search(px, py, bullets):
    """Run C beam search from bullet data. bullets: list of (x,y,angle_index)."""
    n = len(bullets)
    bx = (ctypes.c_int * n)(*[b[0] for b in bullets])
    by = (ctypes.c_int * n)(*[b[1] for b in bullets])
    ai = (ctypes.c_int * n)(*[b[2] for b in bullets])
    return _lib.sim_beam_search_raw(px, py, n, bx, by, ai)
