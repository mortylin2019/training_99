"""
simulator/engine.py - GameSimulator matching decompiled C exactly.

Game_Init (FUN_00404660) + Stage2_GameEntityLoop (FUN_00402fbc)
+ Bullet Spawning (FUN_00402e88) + Angle Aiming (FUN_00402d68).

All constants in config.py — single source of truth.
"""
from .config import *
from .rng import LCG
from .bullet import Bullet, move_bullet
import math


class GameSimulator:
    """Faithful 99.exe game engine."""

    def __init__(self, difficulty=1, seed=0, spawn_interval_ms=None):
        self.rng = LCG(seed)
        self.start_bullets = DIFF_BULLETS.get(difficulty, 50)
        self._spawn_interval = (int(spawn_interval_ms * FPS / 1000)
                                if spawn_interval_ms else SPAWN_INTERVAL)
        self.reset()

    def reset(self):
        """Game_Init (FUN_00404660): init entity array and game state."""
        self.px = PLAYER_START_X
        self.py = PLAYER_START_Y
        self.frame = 0
        self.dead = False

        self.bullet_count = self.start_bullets
        self.next_spawn = self._spawn_interval  # C: DAT_00406dfc = G_GameStartTime + 3000
        self.next_pattern = PATTERN_CHECK  # first pattern check in 5s
        self.pattern = 0
        self.bounce_limit = 0

        # Graze state
        self.active_near = 0       # G_ActiveEntityCount (0x00406db4)
        self.graze_total = 0       # G_TotalEntitiesSpawned (0x00406db8)
        self._graze_chain = 0      # G_PatternCounter (0x00406e0c, 1-10)
        self._graze_chain_time = 0  # chain window timer

        # 300 slots, all inactive (C: do { slot[2]=0xff; } while(i<300))
        self.bullets = [Bullet(angle_index=INACTIVE) for _ in range(MAX_ENTITIES)]

        # No pre-fill: GameInit only marks slots inactive (angle_index=0xFF).
        # Bullets spawn one-per-frame via EntityLoop spawn boundary (step()).

    # ── FUN_00402d68: Compute aimed angle ─────────────────
    def _aimed_angle(self, bullet_raw_x, bullet_raw_y, spread):
        """FUN_00402d68 — EXACT assembly-verified octant search."""
        from .functions import compute_aimed_angle
        # Use engine's RNG state (extract from LCG object)
        rng_state = self.rng.state
        rng_state, angle = compute_aimed_angle(
            bullet_raw_x, bullet_raw_y, self.px, self.py,
            rng_state, spread)
        self.rng.state = rng_state
        return angle

    # ── FUN_00402e88: Spawn one bullet ────────────────────
    def _spawn_at(self, slot):
        """Entity_SpawnBullet — recycle slot in-place."""
        b = self.bullets[slot]
        edge = self.rng.next() & (SPAWN_EDGES - 1)

        if edge == 0:    # Top edge
            b.raw_x = self.rng.next() % SPAWN_RANGE_X
            b.raw_y = 0
        elif edge == 1:  # Bottom edge
            b.raw_x = self.rng.next() % SPAWN_RANGE_X
            b.raw_y = RAW_MAX_Y
        elif edge == 2:  # Left edge
            b.raw_x = 0
            b.raw_y = self.rng.next() % SPAWN_RANGE_Y
        else:            # Right edge
            b.raw_x = RAW_MAX_X
            b.raw_y = self.rng.next() % SPAWN_RANGE_Y

        info = PATTERN_INFO.get(self.pattern, PATTERN_INFO[0])
        b.type = info["type"]
        b.timer = info["timer"]
        b.counter = 0
        b.grazed = 0
        b.vx = 0
        b.vy = 0

        # Pattern 5: random homing timer (C: ((RNG&3)+1)*16)
        if self.pattern == 5:
            b.timer = ((self.rng.next() & 3) + 1) * 16

        # Pattern 7: H-Accel, no aiming (vx=vy=0, returns early)
        # When bounce_limit >= MAX_BOUNCE: fall through to Type 0 with aiming
        if self.pattern == 7:
            if self.bounce_limit >= MAX_BOUNCE:
                b.type = TYPE_NORMAL
                # FALL THROUGH to aimed spawn below
            else:
                self.bounce_limit += 1
                b.angle_index = 0
                return

        # AIMED spawn (FUN_00402d68)
        spread = info.get("spread", 5)
        b.angle_index = self._aimed_angle(b.raw_x, b.raw_y, spread)

    # ── Stage2_GameEntityLoop: one frame ──────────────────
    def step(self, input_bits):
        """
        One frame: player move + entity loop + spawning + patterns.
        input_bits: 0-12 G_InputState bitmask (1=LEFT,2=UP,4=DOWN,8=RIGHT).
        Returns (alive, visible_bullets).
        """
        if self.dead:
            return False, []

        self.frame += 1

        # Entity loop (FUN_00402fbc: do { ... } while(true))
        # Player movement happens AFTER entity loop (matching real game order:
        # MainFrame calls FUN_00402fbc first, then applies input second).
        # This means newly spawned bullets aim at the player's OLD position,
        # making dodging slightly harder (and matching the real game).
        active = []
        i = 0
        while i < MAX_ENTITIES:
            b = self.bullets[i]

            # Spawn boundary (C: if (DAT_00406da8 <= local_24))
            if i >= self.bullet_count:
                # Spawn check (C: timer expired && count < 299 && pattern != 7)
                if (self.bullet_count < MAX_BULLETS
                        and self.frame > self.next_spawn
                        and self.pattern != 7):
                    self._spawn_at(i)
                    self.bullet_count += 1
                    self.next_spawn = self.frame + self._spawn_interval

                # Pattern check at boundary (C: even if spawn didn't happen)
                if self.frame > self.next_pattern:
                    if self.pattern == 0:
                        r = self.rng.next()
                        if r < PATTERN_CHANCE:
                            self.pattern = (r % 7) + 1  # r2: mov eax,[esp+8] reuses same RNG value
                            self.next_pattern = self.frame + PATTERN_ACTIVE
                        else:
                            self.next_pattern = self.frame + PATTERN_CHECK
                    else:
                        self.pattern = 0
                        self.next_pattern = self.frame + PATTERN_CHECK
                break  # C: return

            # Inactive slot → respawn exactly ONE (C: if (uVar6==0xff) {spawn; return;})
            if b.angle_index == INACTIVE:
                self._spawn_at(i)
                self._apply_input(input_bits)
                return not self.dead, active

            # Off-screen check BEFORE move (asm at 0x40300E: cmp raw_x,0x5100; ja)
            # Mask to 32-bit unsigned for negative raw_x/raw_y (bullets off left/top edges)
            if (b.raw_x & 0xFFFFFFFF) >= RAW_MAX_X or (b.raw_y & 0xFFFFFFFF) >= RAW_MAX_Y:
                if b.type & 2:  # type 2 (H-Accel) or 3 (Accel) — asm: test [ecx+0xa],2
                    self.bounce_limit -= 1
                self._spawn_at(i)
                i += 1
                continue

            # Move bullet (C: type-specific movement)
            move_bullet(b, self.px, self.py, self.rng)

            # Graze + collision (C: only when G_GameOverFlag == 0)
            if not self.dead:
                bpx = (b.raw_x >> RAW_SHIFT) - PIXEL_OFFSET
                bpy = (b.raw_y >> RAW_SHIFT) - PIXEL_OFFSET
                dx_b = bpx - self.px
                dy_b = bpy - self.py

                # Graze proximity (C: dx+4 < 0x17 AND dy+6 < 0x14)
                if dx_b + 4 < GRAZE_DX and dy_b + 6 < GRAZE_DY:
                    if not b.grazed:
                        b.grazed = 1
                        self.active_near += 1
                    # Collision (C: dx-2 < 0xb AND dy < 10)
                    if (dx_b - HIT_X1 >= 0 and dx_b < HIT_X2
                            and dy_b >= HIT_Y1 and dy_b < HIT_Y2):
                        self.dead = True
                elif b.grazed:
                    # Bullet leaves graze zone (C: else if grazed)
                    b.grazed = 0
                    self.active_near -= 1
                    if self.active_near > 0:
                        self.graze_total += self.active_near
                        # Graze chain (C: DAT_00406e08 / DAT_00406e0c)
                        if self.frame < self._graze_chain_time:
                            if self._graze_chain < GRAZE_CHAIN_MAX:
                                self._graze_chain += 1
                        else:
                            self._graze_chain = 1
                        self._graze_chain_time = self.frame + GRAZE_WINDOW

            if not self.dead:
                active.append(b)
            i += 1

        self._apply_input(input_bits)
        return not self.dead, active

    def _apply_input(self, input_bits):
        """Apply player movement from input bitmask (FUN_00403400)."""
        dx = (1 if input_bits & 8 else 0) - (1 if input_bits & 1 else 0)
        dy = (1 if input_bits & 4 else 0) - (1 if input_bits & 2 else 0)
        self.px = max(0, min(SCR_W, self.px + dx))
        self.py = max(0, min(SCR_H, self.py + dy))

    def get_visible_bullets(self):
        """Return active bullets for AI decision."""
        return [b for b in self.bullets[:self.bullet_count]
                if b.angle_index != INACTIVE]
