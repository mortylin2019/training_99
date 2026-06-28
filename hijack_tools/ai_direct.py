"""
ai_direct.py — Superior Survival AI using Full Game State Hijack

Reads ALL available game data from decompiled memory addresses:
- Player position, bullet array, velocity tables
- Pattern info (what pattern is active, duration remaining)
- Spawn timing (when next bullets arrive)

Control: Writes input bitmask directly to G_InputState (0x00406d7c).
This is TRUE process hijack — NO keyboard SendMessage, NO teleportation.
The game reads this bitmask each frame and moves player 1px/frame.

Algorithm: Two-Pass Time-Space Danger Evaluation
  Pass 1 (Immediate): Check frames 1-5 for imminent death → PANIC
  Pass 2 (Strategic): Check frames 8-50 for positioning, center pull
  Uses numpy-vectorized bullet prediction from actual velocity tables.
"""

import time
import math
import numpy as np
from loguru import logger

try:
    from game_control import GameControl
    import keyboard as kbd
except ImportError:
    from hijack_tools.game_control import GameControl
    import hijack_tools.keyboard as kbd


class SuperiorAI:
    """
    Two-pass danger evaluation with exact bullet trajectory prediction.
    Writes to G_InputState — the game's native movement mechanism.
    """

    def __init__(self, game_instance=None):
        self.game = game_instance if game_instance else GameControl()

        # Screen bounds (from decompiled: game clamps PlayerX to [0, 0x130], Y to [0, 0xE0])
        self.SCREEN_W = 0x130
        self.SCREEN_H = 0xE0
        self.CENTER_X = 0x98   # 152 — actual game start X
        self.CENTER_Y = 0x2C   # 44  — actual game start Y

        # Hitbox (Stage2_GameEntityLoop.c):
        #   if ((iVar4 - 2U < 0xb) && (uVar8 < 10)) → collision
        #   iVar4 = bx - px, uVar8 = by - py
        #   So: 2 <= (bx-px) < 13  AND  0 <= (by-py) < 10
        self.HITBOX_X1 = 2
        self.HITBOX_X2 = 13
        self.HITBOX_Y1 = 0
        self.HITBOX_Y2 = 10

        self.PREDICT_FRAMES = 60
        self.MOVE_SPEED = 1

        # Weights
        self.COLLISION = 10_000_000.0
        self.PROXIMITY = 4000.0
        self.CENTER_GRAVITY = 2.0
        self.WALL_FORCE = 3000.0
        self.WALL_MARGIN = 15

        self._last_log = 0.0
        self._log_interval = 2.0

    # ── Vectorized Bullet Prediction ───────────────────────────────

    def predict_all_bullets(self, active):
        """Predict ALL bullet positions: returns (N, FRAMES+1, 2) float32 array."""
        n = len(active)
        if n == 0:
            return np.zeros((0, self.PREDICT_FRAMES + 1, 2), dtype=np.float32)

        paths = np.zeros((n, self.PREDICT_FRAMES + 1, 2), dtype=np.float32)
        ts = np.arange(self.PREDICT_FRAMES + 1, dtype=np.float32)

        for i, b in enumerate(active):
            if b.type == 2:
                vx = b.vx / 64.0
                vy = b.vy / 64.0
            else:
                vx_raw, vy_raw = self.game.get_bullet_velocity(b.angle_index, b.type)
                vx = vx_raw / 64.0
                vy = vy_raw / 64.0

            paths[i, :, 0] = float(b.x) + vx * ts
            paths[i, :, 1] = float(b.y) + vy * ts

        return paths

    # ── Collision Check ────────────────────────────────────────────

    def check_collision(self, px, py, bullets_at_frame):
        """
        Check hitbox vs bullets at a specific frame.
        Returns (hit_count, min_distance).
        """
        if bullets_at_frame.shape[0] == 0:
            return 0, 9999.0

        bx = bullets_at_frame[:, 0]
        by = bullets_at_frame[:, 1]

        dx = bx - px
        dy = by - py
        hits = np.sum(
            (dx >= self.HITBOX_X1) & (dx < self.HITBOX_X2) &
            (dy >= self.HITBOX_Y1) & (dy < self.HITBOX_Y2)
        )

        cx, cy = px + 7.5, py + 5.0
        dists = np.sqrt((bx - cx) ** 2 + (by - cy) ** 2)
        min_d = float(np.min(dists))

        return int(hits), min_d

    # ── Score Position at Frame ────────────────────────────────────

    def score_at_frame(self, px, py, paths, fidx):
        """Score (px,py) at frame fidx. Returns (score, is_fatal)."""
        if fidx >= paths.shape[1]:
            fidx = paths.shape[1] - 1

        hits, min_d = self.check_collision(px, py, paths[:, fidx, :])
        if hits > 0:
            return self.COLLISION + hits, True

        danger = self.PROXIMITY / max(min_d * min_d, 1.0)

        # Center gravity
        dc = math.sqrt((px - self.CENTER_X) ** 2 + (py - self.CENTER_Y) ** 2)
        danger += dc * self.CENTER_GRAVITY

        # Walls
        if px < self.WALL_MARGIN:
            danger += (self.WALL_MARGIN - px) * self.WALL_FORCE
        elif px > self.SCREEN_W - self.WALL_MARGIN:
            danger += (px - (self.SCREEN_W - self.WALL_MARGIN)) * self.WALL_FORCE
        if py < self.WALL_MARGIN:
            danger += (self.WALL_MARGIN - py) * self.WALL_FORCE
        elif py > self.SCREEN_H - self.WALL_MARGIN:
            danger += (py - (self.SCREEN_H - self.WALL_MARGIN)) * self.WALL_FORCE

        return danger, False

    # ── Evaluate Move ──────────────────────────────────────────────

    def eval_move(self, px, py, dx, dy, paths):
        """
        Two-pass evaluation of a direction.
        Returns (total_score, is_fatal).
        """
        immediate = [1, 2, 3, 4, 5]
        strategic = [8, 12, 18, 25, 35, 50]

        score = 0.0
        fatal = False

        # Pass 1: Immediate survival (HEAVY weight)
        for f in immediate:
            fx = max(0, min(self.SCREEN_W, px + dx * self.MOVE_SPEED * f))
            fy = max(0, min(self.SCREEN_H, py + dy * self.MOVE_SPEED * f))
            s, is_fatal = self.score_at_frame(fx, fy, paths, f)
            w = 1.0 / (f * 0.3 + 0.3)
            score += s * w
            if is_fatal:
                fatal = True

        # Pass 2: Strategic (only if not dying)
        if not fatal:
            for f in strategic:
                fx = max(0, min(self.SCREEN_W, px + dx * self.MOVE_SPEED * f))
                fy = max(0, min(self.SCREEN_H, py + dy * self.MOVE_SPEED * f))
                s, _ = self.score_at_frame(fx, fy, paths, f)
                w = 1.0 / (1.0 + f * 0.06)
                score += s * w

        return score, fatal

    # ── Perform Move ───────────────────────────────────────────────

    MOVE_TABLE = [
        ( 0,  0, 0),   # STOP
        (-1,  0, 1),   # LEFT
        ( 1,  0, 8),   # RIGHT
        ( 0, -1, 2),   # UP
        ( 0,  1, 4),   # DOWN
        (-1, -1, 3),   # UP-LEFT
        (-1,  1, 5),   # DOWN-LEFT
        ( 1, -1, 10),  # UP-RIGHT
        ( 1,  1, 12),  # DOWN-RIGHT
    ]

    def perform_move(self):
        """Read state → predict → evaluate → write bitmask."""
        px, py = self.game.get_player_pos()
        if px <= 0 or py <= 0:
            px, py = self.CENTER_X, self.CENTER_Y

        bullets = self.game.get_bullets()
        active = [b for b in bullets if b.angle_index != 0xFF]

        if not active:
            self.game.write_int(0x00406d7c, 0)
            return

        paths = self.predict_all_bullets(active)

        best_score = float('inf')
        best_bits = 0
        panic = False

        for dx, dy, bits in self.MOVE_TABLE:
            score, fatal = self.eval_move(px, py, dx, dy, paths)
            if fatal:
                panic = True
            if score < best_score:
                best_score = score
                best_bits = bits

        # Periodic log
        now = time.time()
        if now - self._last_log > self._log_interval:
            pat = self.game.get_next_pattern()
            grz = self.game.get_active_near()
            t = self.game.get_game_time()
            mult = self.game.get_score_multiplier()
            label = "PANIC" if panic else "SAFE"
            ms = t / (mult or 1) * 12.5  # approx ms @80fps with mult=16
            logger.info(
                f"[{label}] P:{px:>3},{py:>3} B:{len(active):>3} "
                f"Pat:{pat} Grz:{grz} → {kbd.get_key_name(best_bits):>8} "
                f"score={best_score:.0f} | {ms:.0f}ms"
            )
            self._last_log = now

        self.game.write_int(0x00406d7c, best_bits)


# ── Auto-Restart Entry Point ──────────────────────────────────────

if __name__ == "__main__":
    import sys
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("logs/ai_direct.log", rotation="10 MB", retention="5 days", level="DEBUG")

    game = GameControl()
    if not game.launch_game():
        logger.error("Failed to launch game")
        sys.exit(1)

    ai = SuperiorAI(game)
    logger.info("ai_direct — bitmask hijack, auto start/retry. Ctrl+C to stop.")

    in_run = False
    try:
        while True:
            is_playing = game.is_playing()
            is_dead = game.is_game_over()

            # ── Run start ──
            if is_playing and not is_dead and not in_run:
                in_run = True
                logger.success("=== NEW RUN ===")

            # ── Run end ──
            if in_run and (not is_playing or is_dead):
                in_run = False
                ms = game.get_survival_ms()
                t = game.get_game_time()
                m = game.get_score_multiplier() or 1
                logger.success(
                    f"=== DEAD | {ms}ms ({ms/1000:.1f}s) | "
                    f"Frames:{t} | Mult:{m} ==="
                )
                game.write_int(0x00406d7c, 0)
                time.sleep(0.3)  # Let death animation play

            # ── Auto-navigate menus ──
            if not is_playing:
                game.write_int(0x00406d7c, 0)
                game.press_enter()
                time.sleep(0.15)
                continue

            # ── Active gameplay ──
            if in_run and is_playing:
                ai.perform_move()

    except KeyboardInterrupt:
        game.write_int(0x00406d7c, 0)
        logger.info("AI stopped by user.")
    finally:
        game.cleanup()
