"""
ai_mcts.py — Progressive Widening AI for 特訓９９.
Uses heuristic filter + parallel guided rollouts to pick the best move.
Pure Rust/PyO3 backend via beam_core.

Architecture:
  1. Heuristic filter: 4 probe timesteps × 9 moves → rank by cumulative danger
  2. Adaptive top-k: keep candidates within 5× of best score (1-3 candidates)
  3. Parallel guided rollouts: low-τ softmax policy across candidates (rayon)
  4. Pick the move with lowest average rollout danger

Also available: UCB1 MCTS tree (mcts_ucb) — experimental, underperforms filter+rollout.

Config: see algo_config.py (MCTS_* constants)
"""
import numpy as np
import sys
import os

_BEAM_CORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beam_core')
if os.path.isdir(_BEAM_CORE_DIR) and _BEAM_CORE_DIR not in sys.path:
    sys.path.insert(0, _BEAM_CORE_DIR)

from beam_core import guided_mcts_score_py as _guided_mcts_score
from beam_core import mcts_ucb_py as _mcts_ucb
from beam_core import mcts_progressive_py as _mcts_progressive
from beam_core import max_gap_move_py as _max_gap_move
from beam_core import score_pos_py as _score_pos


class MctSAI:
    """Progressive widening AI: heuristic filter + parallel guided rollouts."""

    def __init__(self, vel_table=None, accel_table=None):
        self.vel_table = np.array(vel_table or [(0, 0)], dtype=np.float32)
        self.accel_table = np.array(accel_table or [(0, 0)], dtype=np.float32)

    def _velocity(self, angles):
        idx = np.clip((angles & 0x3F).astype(np.int32), 0, len(self.vel_table) - 1)
        return self.vel_table[idx] / 64.0

    def _config_kwargs(self):
        try:
            import hijack_tools.algo_config as c
        except ImportError:
            import algo_config as c
        return dict(
            beam_depth=20, beam_width=c.BEAM_WIDTH,  # 20-frame sweet spot for guided rollouts
            check_every=1,  # fine-grained stepping essential for softmax quality
            danger_base=c.DANGER_BASE, safety_margin=c.SAFETY_MARGIN,
            wall_penalty=c.WALL_PENALTY, wall_margin=c.WALL_MARGIN,
            tw_base=c.TIME_WEIGHT_BASE, tw_rate=c.TIME_WEIGHT_RATE,
            early_exit_enabled=c.EARLY_EXIT_ENABLED,
            early_exit_buffer=c.EARLY_EXIT_BUFFER,
            partial_sort_enabled=c.PARTIAL_SORT_ENABLED,
            center_pull_enabled=c.CENTER_PULL_ENABLED,
            wall_penalty_enabled=c.WALL_PENALTY_ENABLED,
            directional_weight=0.0,  # DW hurts MCTS (overreacts to moving bullets)
        )

    def _predict(self, bullets, px=0, py=0):
        try:
            import hijack_tools.algo_config as c
        except ImportError:
            import algo_config as c
        n = len(bullets)
        T = 21  # beam_depth=20 + 1, each timestep covers check_every=4 real frames
        if n == 0:
            return np.zeros((0, T, 2), dtype=np.float64)

        bx = np.array([b.x for b in bullets], dtype=np.float64)
        by = np.array([b.y for b in bullets], dtype=np.float64)
        types = np.array([b.type for b in bullets], dtype=np.int32)
        ang = np.array([b.angle_index for b in bullets], dtype=np.int32)

        vel = self._velocity(ang)
        ts = np.arange(T, dtype=np.float64)  # CE=1: paths[t] = bullet at real frame t
        paths = np.zeros((n, T, 2), dtype=np.float64)
        paths[:, :, 0] = bx[:, None] + vel[:, 0, None] * ts[None, :]
        paths[:, :, 1] = by[:, None] + vel[:, 1, None] * ts[None, :]

        if not c.USE_TYPE_PREDICTION:
            return paths

        t2_mask = types == 2
        if t2_mask.any():
            vx = np.array([b.vx for b in bullets], dtype=np.float64) / 64.0
            vy = np.array([b.vy for b in bullets], dtype=np.float64) / 64.0
            vel[t2_mask, 0] = vx[t2_mask]
            vel[t2_mask, 1] = vy[t2_mask]
            paths[:, :, 0] = bx[:, None] + vel[:, 0, None] * ts[None, :]
            paths[:, :, 1] = by[:, None] + vel[:, 1, None] * ts[None, :]

        t3_mask = types == 3
        if t3_mask.any() and len(self.accel_table) >= 64:
            ang_idx = np.clip((ang[t3_mask] & 0x3F).astype(np.int32),
                              0, len(self.accel_table) - 1)
            accel_vel = self.accel_table[ang_idx] / 64.0
            vel[t3_mask, 0] = accel_vel[:, 0]
            vel[t3_mask, 1] = accel_vel[:, 1]
            paths[:, :, 0] = bx[:, None] + vel[:, 0, None] * ts[None, :]
            paths[:, :, 1] = by[:, None] + vel[:, 1, None] * ts[None, :]

        t1_mask = types == 1
        if t1_mask.any():
            for i in np.where(t1_mask)[0]:
                timer = getattr(bullets[i], 'timer', 48)
                if timer <= 0:
                    continue
                cx = bx[i]
                cy = by[i]
                cur_ang = ang[i]
                for t in range(1, T):
                    if t % timer == 0:
                        tdx = px - cx
                        tdy = py - cy
                        ang_rad = np.arctan2(tdy, tdx)
                        cur_ang = int(((ang_rad / (2 * np.pi) * 64) + 64.5) % 64)
                    idx = cur_ang & 63
                    cx += self.vel_table[idx, 0] / 64.0
                    cy += self.vel_table[idx, 1] / 64.0
                    paths[i, t, 0] = cx
                    paths[i, t, 1] = cy

        t2_mask = types == 2
        if t2_mask.any():
            for i in np.where(t2_mask)[0]:
                cx = bx[i]
                cy = by[i]
                cvx = bullets[i].vx
                cvy = bullets[i].vy
                for t in range(1, T):
                    if cx < px:
                        cvx += 1
                    elif cx > px:
                        cvx -= 1
                    if cy < py:
                        cvy += 1
                    elif cy > py:
                        cvy -= 1
                    if cvx > 96:
                        cvx = 96
                    elif cvx < -96:
                        cvx = -96
                    if cvy > 96:
                        cvy = 96
                    elif cvy < -96:
                        cvy = -96
                    cx += cvx / 64.0
                    cy += cvy / 64.0
                    paths[i, t, 0] = cx
                    paths[i, t, 1] = cy

        return paths

    def decide(self, px, py, bullets):
        try:
            import hijack_tools.algo_config as c
        except ImportError:
            import algo_config as c
        if not bullets:
            return 0
        if px <= 0 or py <= 0:
            px, py = c.CTR_X, c.CTR_Y

        paths = self._predict(bullets, px, py)
        kw = self._config_kwargs()
        best = int(_mcts_progressive(
            float(px), float(py), paths,
            0, 0,  # filter_width, filter_depth (unused — heuristic filter is hardcoded)
            c.MCTS_TOP_K, c.MCTS_ITERATIONS,
            c.MCTS_TAU_START, c.MCTS_TAU_END,
            c.MCTS_VERIFY_TAU, **kw,
        )[0])

        if best <= 0 or best > 8:
            bullets_arr = np.array([(b.x, b.y) for b in bullets], dtype=np.float64)
            best = _max_gap_move(float(px), float(py), bullets_arr)
        return int(c.BITS[max(best, 0) % len(c.BITS)])
