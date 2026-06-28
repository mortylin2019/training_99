"""
game_control.py — Pure memory I/O layer for 99.exe process hijack.

Provides:
  - Process launch, attach, cleanup
  - Memory read/write (ReadProcessMemory / WriteProcessMemory)
  - Game state readers (player pos, bullets, patterns, timing, etc.)
  - Velocity table readers
  - Window detection (EnumWindows by PID)
  - Input: keybd_event for menu navigation

NO game loop, NO AI logic, NO logging configuration here.
"""

import ctypes
import time
import subprocess
import os
import struct
from loguru import logger

try:
    from bullet_data import Bullet
    import keyboard as kbd
except ImportError:
    from hijack_tools.bullet_data import Bullet
    import hijack_tools.keyboard as kbd

# Windows Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
VK_RETURN = 0x0D

# Input event constants for keybd_event
KEYEVENTF_KEYUP = 0x0002

# ============================================================================
# Game Memory Map — ALL known addresses from reverse engineering
# ============================================================================

# --- Player State ---
ADDR_PLAYER_X        = 0x00406d6c  # G_PlayerX (pixels, writeable!)
ADDR_PLAYER_Y        = 0x00406d70  # G_PlayerY (pixels, writeable!)
ADDR_INPUT_STATE     = 0x00406d7c  # G_InputState (bitmask, writeable)

# --- Game State Machine ---
ADDR_GAME_STATE      = 0x00406d74  # 0=Title, 1=Playing, 2=SubMenu, 3=SubMenu, 4=SubMenu, 5=Result, 6=Ranking
ADDR_SUB_STATE       = 0x00406d78  # G_SubState — sub-menu position
ADDR_GAME_OVER       = 0x00406d80  # G_GameOverFlag (0=alive, 1=dead; increments 1→0x11 during death anim)
ADDR_PAUSE_FLAG      = 0x00406d84  # G_PauseFlag (1=Active/Playing, 0=Paused/Menu)
ADDR_IS_GAME_RUNNING = 0x00406d90  # G_IsGameRunning (1=running)

# --- Timing ---
ADDR_GAME_TIME       = 0x00406d88  # G_Score_Time — frame counter (incremented each frame alive)
ADDR_SCORE_MULTIPLIER= 0x00406d8c  # G_ScoreMultiplier: 16(Std), 12(Mode2), 0(Mode3)
ADDR_GAME_START_TIME = 0x00406d94  # G_GameStartTime — timeGetTime() at session start
ADDR_DEATH_TIME      = 0x00406d98  # G_DeathTime — timeGetTime() when player died
ADDR_CURRENT_TICK    = 0x00406da4  # G_CurrentTime_Tick — current timeGetTime()
ADDR_PAUSE_ACCUM     = 0x00406da0  # Pause-adjusted time accumulator
ADDR_TABOUT_FLAG     = 0x00406d9c  # Window focus flag (0=focused, else=tabbed out)

# --- Entity / Bullet System ---
ADDR_BULLET_COUNT    = 0x00406da8  # G_CurrentBulletCount — active bullet count
ADDR_BOUNCE_LIMIT    = 0x00406dac  # Bounce bullet limit counter (max 4, then stops spawning Type 2)
ADDR_ACTIVE_NEAR     = 0x00406db4  # G_ActiveEntityCount — bullets in graze proximity
ADDR_GRAZE_TOTAL     = 0x00406db8  # G_TotalEntitiesSpawned — accumulated graze score
ADDR_ENTITY_ARRAY    = 0x00406e10  # G_EntityArray — 300 × 15 byte bullet entities
ENTITY_SIZE          = 15

# --- Bullet Pattern / Spawning ---
ADDR_NEXT_PATTERN    = 0x00406dbc  # G_NextBulletPattern — current pattern (0=none, 1-7=active pattern)
ADDR_PATTERN_DURATION= 0x00406db0  # G_PatternDuration — remaining frames for current pattern
ADDR_PATTERN_COUNTER = 0x00406dc0  # G_SomePatternCounter — graze-based pattern counter
ADDR_GRAZE_PAT_CTR   = 0x00406df0  # G_PatternCounter — graze chain counter (1-10)
ADDR_PATTERN_TIMER2  = 0x00406e00  # G_PatternTimer2 — timer for graze chain reset
ADDR_NEXT_SPAWN_TIME = 0x00406dfc  # G_NextSpawnTime — timestamp for next bullet spawn
ADDR_NEXT_PATTERN_TIME=0x00406e00  # G_NextPatternTime — timestamp for pattern change

# --- Difficulty / Mode ---
ADDR_DIFFICULTY      = 0x00406dc0  # G_DifficultyMode: 0=Easy(30), 1=Normal(50), 2=Hard(100), 3=Lunatic(200)
ADDR_BG_MODE         = 0x00406dc4  # Background mode: 0=off, 1=grayscale, 2=noise
ADDR_SCORE_TYPE      = 0x00406dc8  # G_ScoreType: 0, 1, 2
ADDR_HIGH_PRIORITY   = 0x00406dcc  # G_HighPriorityMode

# --- Lookup Tables (read once at init) ---
ADDR_VEL_TABLE       = 0x00405d74  # Type 0/1 velocity table: 64 angles × 12 bytes (vx:4, vy:4, ?:4)
ADDR_ACCEL_TABLE     = 0x00406074  # Type 3 acceleration table: 64 angles × 12 bytes
VEL_ENTRY_SIZE       = 12
NUM_ANGLES           = 64

# --- Pattern Display (UI elements) ---
ADDR_PATTERN_BAR_X   = 0x00406df4  # Pattern bar X offset
ADDR_PATTERN_BAR_W   = 0x00406df8  # Pattern bar width per unit

class GameControl:
    """Pure memory I/O layer — no game loop, no AI logic."""
    
    def __init__(self, exe_path=r"C:\git\training_99\raw\99.exe"):
        self.exe_path = exe_path
        self.process_handle = None
        self.pid = None
        self.hwnd = None
        self.proc = None
        
        # Velocity Tables (read from game memory once at init)
        self.vel_table = []
        self.accel_table = []

    # ── Lookup Tables ──────────────────────────────────────────────
    
    def _read_tables(self):
        """Reads the velocity and acceleration tables from the game binary data."""
        if not self.process_handle: return
        
        # Table 1: Type 0, 1 Velocity (64 angles × 12 bytes: vx:i32, vy:i32, ?:i32)
        data = self.read_memory(ADDR_VEL_TABLE, NUM_ANGLES * VEL_ENTRY_SIZE)
        if data:
            self.vel_table = []
            for i in range(NUM_ANGLES):
                vx, vy = struct.unpack("<ii", data[i*VEL_ENTRY_SIZE : i*VEL_ENTRY_SIZE+8])
                self.vel_table.append((vx, vy))
                
        # Table 2: Type 3 Acceleration (64 angles × 12 bytes)
        data = self.read_memory(ADDR_ACCEL_TABLE, NUM_ANGLES * VEL_ENTRY_SIZE)
        if data:
            self.accel_table = []
            for i in range(NUM_ANGLES):
                vx, vy = struct.unpack("<ii", data[i*VEL_ENTRY_SIZE : i*VEL_ENTRY_SIZE+8])
                self.accel_table.append((vx, vy))
    
    # ── Convenience typed readers ──────────────────────────────────
    
    def read_float(self, address):
        """Reads a 4-byte float from process memory."""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack("<f", data)[0]
        return None
    
    def read_byte(self, address):
        """Reads a single byte from process memory."""
        data = self.read_memory(address, 1)
        if data:
            return data[0]
        return None
    
    # ── Player State ───────────────────────────────────────────────
    
    def get_player_pos(self):
        """Returns (x, y) pixel coordinates of the player."""
        x_raw = self.read_int(ADDR_PLAYER_X)
        y_raw = self.read_int(ADDR_PLAYER_Y)
        if x_raw is None or y_raw is None: return 0, 0
        return x_raw, y_raw
    
    # ── Game State ─────────────────────────────────────────────────
    
    def get_game_state(self):
        """Returns game state: 0=Title, 1=Playing, 2-4=SubMenus, 5=Result, 6=Ranking."""
        return self.read_int(ADDR_GAME_STATE)
    
    def get_sub_state(self):
        """Returns sub-state for menu navigation."""
        return self.read_int(ADDR_SUB_STATE)
    
    def is_game_over(self):
        """Returns True if player is dead."""
        return self.read_int(ADDR_GAME_OVER) != 0
    
    def is_playing(self):
        """Returns True if game is actively playing (PauseFlag == 1)."""
        return self.read_int(ADDR_PAUSE_FLAG) == 1
    
    def is_running(self):
        """Returns True if G_IsGameRunning == 1."""
        return self.read_int(ADDR_IS_GAME_RUNNING) == 1
    
    # ── Timing ─────────────────────────────────────────────────────
    
    def get_game_time(self):
        """Returns G_Score_Time — raw frame counter."""
        return self.read_int(ADDR_GAME_TIME) or 0
    
    def get_score_multiplier(self):
        """Returns G_ScoreMultiplier (16, 12, or 0)."""
        return self.read_int(ADDR_SCORE_MULTIPLIER) or 16
    
    def get_start_time(self):
        """Returns G_GameStartTime — timeGetTime() when session began."""
        return self.read_int(ADDR_GAME_START_TIME) or 0
    
    def get_death_time(self):
        """Returns G_DeathTime — timeGetTime() when player died (0 if alive)."""
        return self.read_int(ADDR_DEATH_TIME) or 0
    
    def get_current_tick(self):
        """Returns G_CurrentTime_Tick — current timeGetTime()."""
        return self.read_int(ADDR_CURRENT_TICK) or 0
    
    def get_survival_ms(self):
        """Returns actual survival time in milliseconds."""
        death = self.get_death_time()
        start = self.get_start_time()
        if death and start:
            return death - start
        tick = self.get_current_tick()
        if tick and start:
            return tick - start
        return 0
    
    # ── Bullet / Entity System ─────────────────────────────────────
    
    def get_bullet_count(self):
        """Returns G_CurrentBulletCount — number of active bullets."""
        return self.read_int(ADDR_BULLET_COUNT) or 0
    
    def get_bounce_limit(self):
        """Returns bounce bullet limit counter (max 4)."""
        return self.read_int(ADDR_BOUNCE_LIMIT) or 0
    
    def get_active_near(self):
        """Returns G_ActiveEntityCount — bullets in graze proximity to player."""
        return self.read_int(ADDR_ACTIVE_NEAR) or 0
    
    def get_graze_total(self):
        """Returns G_TotalEntitiesSpawned — accumulated graze score."""
        return self.read_int(ADDR_GRAZE_TOTAL) or 0
    
    # ── Pattern / Spawning ─────────────────────────────────────────
    
    def get_next_pattern(self):
        """Returns G_NextBulletPattern: 0=none, 1-7=active pattern ID."""
        return self.read_int(ADDR_NEXT_PATTERN) or 0
    
    def get_pattern_duration(self):
        """Returns remaining frames for current bullet pattern."""
        return self.read_int(ADDR_PATTERN_DURATION) or 0
    
    def get_graze_pattern_counter(self):
        """Returns G_PatternCounter — graze chain (1-10)."""
        return self.read_int(ADDR_GRAZE_PAT_CTR) or 0
    
    def get_next_spawn_time(self):
        """Returns G_NextSpawnTime — timestamp for next bullet spawn."""
        return self.read_int(ADDR_NEXT_SPAWN_TIME) or 0
    
    def get_next_pattern_time(self):
        """Returns G_NextPatternTime — timestamp for pattern change."""
        return self.read_int(ADDR_NEXT_PATTERN_TIME) or 0
    
    # ── Difficulty / Mode ──────────────────────────────────────────
    
    def get_difficulty(self):
        """Returns difficulty: 0=Easy(30), 1=Normal(50), 2=Hard(100), 3=Lunatic(200)."""
        return self.read_int(ADDR_DIFFICULTY) or 0
    
    def get_bg_mode(self):
        """Returns background mode: 0=off, 1=grayscale, 2=noise."""
        return self.read_int(ADDR_BG_MODE) or 0
    
    # ── Full Snapshot (single read burst for performance) ──────────
    
    def get_full_snapshot(self):
        """
        Reads ALL game state in one contiguous memory sweep.
        Returns a dict with all game state for AI decision-making.
        
        Memory layout (0x00406d6c through 0x00406dd0, approx 100 bytes):
        This covers PlayerX through the pattern/mode variables.
        """
        # Read a block covering all critical addresses
        # From PlayerX (0x00406d6c) through HighPriorityMode (0x00406dcc+4)
        SNAPSHOT_START = 0x00406d6c
        SNAPSHOT_SIZE = 0x64  # 100 bytes covers everything we need
        
        raw = self.read_memory(SNAPSHOT_START, SNAPSHOT_SIZE)
        if not raw:
            return None
        
        # Unpack all 4-byte aligned values
        # Offsets relative to SNAPSHOT_START (0x00406d6c)
        vals = struct.unpack("<25I", raw)  # 25 uint32s
        
        return {
            # Offset 0x00-0x08
            'player_x':          vals[0],   # 0x00406d6c
            'player_y':          vals[1],   # 0x00406d70
            'game_state':        vals[2],   # 0x00406d74
            'sub_state':         vals[3],   # 0x00406d78
            # Offset 0x10-0x20
            'input_state':       vals[4],   # 0x00406d7c
            'game_over':         vals[5],   # 0x00406d80
            'pause_flag':        vals[6],   # 0x00406d84
            'game_time':         vals[7],   # 0x00406d88
            # Offset 0x20-0x30
            'score_multiplier':  vals[8],   # 0x00406d8c
            'is_running':        vals[9],   # 0x00406d90
            'game_start_time':   vals[10],  # 0x00406d94
            'death_time':        vals[11],  # 0x00406d98
            # Offset 0x30-0x44
            'tabout_flag':       vals[12],  # 0x00406d9c
            'pause_accum':       vals[13],  # 0x00406da0
            'current_tick':      vals[14],  # 0x00406da4
            'bullet_count':      vals[15],  # 0x00406da8
            # Offset 0x44-0x54
            'bounce_limit':      vals[16],  # 0x00406dac
            'pattern_duration':  vals[17],  # 0x00406db0
            'active_near':       vals[18],  # 0x00406db4
            'graze_total':       vals[19],  # 0x00406db8
            # Offset 0x54-0x64
            'next_pattern':      vals[20],  # 0x00406dbc
            'difficulty':        vals[21],  # 0x00406dc0
            'bg_mode':           vals[22],  # 0x00406dc4
            'score_type':        vals[23],  # 0x00406dc8
            'high_priority':     vals[24],  # 0x00406dcc
        }
    
    # ── Bullet Velocity Prediction ─────────────────────────────────
    
    def get_bullet_velocity(self, angle_index, bullet_type):
        """
        Returns (vx_raw, vy_raw) for a bullet given its angle_index and type.
        These are RAW internal units — divide by 64 to get pixels/frame.
        """
        idx = angle_index & 0x3F  # 64-angle table
        if bullet_type == 3:  # Accelerating
            if idx < len(self.accel_table):
                return self.accel_table[idx]
        else:  # Type 0 (Normal), Type 1 (Homing base), Type 2 (Bounce initial)
            if idx < len(self.vel_table):
                return self.vel_table[idx]
        return (0, 0)
    
    def predict_bullet_pos(self, bullet, frames_ahead):
        """
        Predicts where a bullet will be N frames from now.
        Returns (px, py) in pixel coordinates.
        Handles Type 0/3 (constant velocity) and Type 2 (bounce with velocity).
        Type 1 (homing) is approximate since it tracks the player.
        """
        if bullet.type == 2:  # Bounce — uses raw vx/vy
            raw_x = bullet.raw_x + bullet.vx * frames_ahead
            raw_y = bullet.raw_y + bullet.vy * frames_ahead
        elif bullet.type == 0 or bullet.type == 3:  # Normal / Accelerating
            vx_raw, vy_raw = self.get_bullet_velocity(bullet.angle_index, bullet.type)
            raw_x = bullet.raw_x + vx_raw * frames_ahead
            raw_y = bullet.raw_y + vy_raw * frames_ahead
        else:  # Type 1 (Homing) — approximate as constant velocity at current angle
            vx_raw, vy_raw = self.get_bullet_velocity(bullet.angle_index, 0)
            raw_x = bullet.raw_x + vx_raw * frames_ahead
            raw_y = bullet.raw_y + vy_raw * frames_ahead
        
        # Convert raw to pixel: pixel = (raw >> 6) - 4
        return ((raw_x >> 6) - 4), ((raw_y >> 6) - 4)
    
    # ── Direct Control (input bitmask hijack, NOT keyboard) ───────
    # Movement is done by writing G_InputState (0x00406d7c) bitmask.
    # The game reads this each frame and moves player 1px/frame in the
    # indicated directions. This is TRUE hijack — no SendMessage/WM_KEYDOWN.

    def launch_game(self):
        """Launches the game and attaches to its process."""
        logger.info(f"Launching {self.exe_path}...")
        try:
            self.proc = subprocess.Popen(self.exe_path, cwd=os.path.dirname(self.exe_path))
            self.pid = self.proc.pid

            # Get process handle first (PID is immediate)
            self.process_handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_ALL_ACCESS, False, self.pid)

            if not self.process_handle:
                logger.error("Failed to open process")
                return False

            logger.success(f"Attached to process PID: {self.pid}")

            # Find window — the game may take a moment to create it
            self.hwnd = self._find_window_by_pid(self.pid)
            if not self.hwnd:
                logger.error("Could not find game window")
                return False

            logger.info(f"Window handle: 0x{self.hwnd:X}")
            self._read_tables()
            return True
        except Exception as e:
            logger.exception(f"Error launching game: {e}")
            return False

    def _find_window_by_pid(self, pid, timeout=5.0):
        """
        Find the main window belonging to a process by enumerating all
        top-level windows and checking their owner PID. Retries until
        the window appears or timeout expires.
        """
        import ctypes.wintypes

        result = []

        @ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                            ctypes.wintypes.HWND,
                            ctypes.wintypes.LPARAM)
        def enum_callback(hwnd, lparam):
            proc_id = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
            if proc_id.value == pid:
                # Check if this is a visible main window (has a title)
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        result.append(hwnd)
                        return False  # Stop enumeration
            return True  # Continue enumeration

        start = time.time()
        while time.time() - start < timeout:
            result.clear()
            ctypes.windll.user32.EnumWindows(enum_callback, 0)
            if result:
                return result[0]
            time.sleep(0.2)

        return None

    def read_memory(self, address, size=4):
        """Reads memory from the process."""
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        if ctypes.windll.kernel32.ReadProcessMemory(self.process_handle, address, buffer, size, ctypes.byref(bytes_read)):
            return buffer.raw
        return None

    def read_int(self, address):
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack("<I", data)[0]
        return None

    def write_memory(self, address, data):
        """Writes data to the process memory."""
        if not self.process_handle: return False
        bytes_written = ctypes.c_size_t()
        return ctypes.windll.kernel32.WriteProcessMemory(
            self.process_handle, address, data, len(data), ctypes.byref(bytes_written)
        )

    def write_int(self, address, value):
        """Writes a 4-byte integer to the process memory."""
        data = struct.pack("<I", value)
        return self.write_memory(address, data)

    def set_input_state(self, bits):
        """Sets the input state and logs it."""
        move_name = kbd.get_key_name(bits)
        
        # We can enable spammy logging here if requested, or just debug
        if bits != 0:
            logger.debug(f"Input Set: {move_name} (Bits: {bits})")
            
        self.write_int(ADDR_INPUT_STATE, bits)

    def get_bullets(self):
        """Reads the bullet/entity array using a single bulk memory read."""
        # The game array is 300 slots of 15 bytes each. 
        # Bulk reading is >100x faster than reading one by one.
        total_size = 300 * ENTITY_SIZE
        raw_data = self.read_memory(ADDR_ENTITY_ARRAY, total_size)
        if not raw_data: return []
        
        px, py = self.get_player_pos()
        bullets = []
        active_count = 0
        
        for i in range(300):
            offset = i * ENTITY_SIZE
            data = raw_data[offset:offset+ENTITY_SIZE]
            
            # Extract raw values: <IIBBBBBbb
            # Offset 8 is raw_vals[2] which is the Slot status.
            # We check data[8] directly for speed before unpacking.
            if data[8] == 0xFF:
                continue
                
            raw_vals = struct.unpack("<IIBBBBBbb", data)
            b = Bullet(*raw_vals) # Use defaults for dist
            b.update_dist(px, py) # Calculate distance to player
            bullets.append(b)
            active_count += 1
            
            # DEBUG: Log every 10th bullet to verify coordinates
            if i % 10 == 0:
                logger.debug(f"P({px},{py}) Bullet[{i}]: X={b.x} Y={b.y} Dist={b.dist_to_player:.1f} Type={b.type}")
                
        return bullets

    def send_key(self, vk_code, duration=0.03):
        """
        Send a key to the game via system-level synthetic input (keybd_event).
        The game uses PeekMessageA and WaitMessage() — keybd_event injects
        into the system input queue, bypassing message encoding issues.
        """
        if not self.hwnd:
            logger.warning("No window handle — cannot send key")
            return
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        time.sleep(0.03)
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        if duration > 0:
            time.sleep(duration)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

    def press_enter(self): self.send_key(VK_RETURN, duration=0.1)

    def cleanup(self):
        """Kills the game process if it is running."""
        if self.proc:
            logger.info(f"Closing game process (PID: {self.pid})...")
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
